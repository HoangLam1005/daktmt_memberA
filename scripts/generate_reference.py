"""Causal trajectory pilot with group splits and per-trajectory refinement gates."""
from pathlib import Path
import json,hashlib,platform,datetime
import numpy as np
from parameters import default_parameters,value
from reference_solver import ReferenceSolver,VERSION
from wheel_interface import reference_step,WheelState,HeldBoundary

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'datasets'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    verification=json.loads((ROOT/'results/verification_metrics.json').read_text())
    if not verification['G1'].startswith('PASS'):raise RuntimeError('G1 prerequisite not met')
    DATA.mkdir(exist_ok=True)
    rng=np.random.default_rng(int(value('seed')));p=default_parameters()
    nx=int(value('nx'));dt=value('dt_solver');duration=value('duration')
    s=ReferenceSolver(p,nx);fine=ReferenceSolver(p,2*nx-1)
    t=np.linspace(0,duration,round(duration/dt)+1)
    tf=np.linspace(0,duration,2*(len(t)-1)+1)
    records=[];forces=[];fields=[];moments=[];slips=[];speeds=[];loads=[];shapes=[];groups=[];splits=[];configs=[]
    for j in range(int(value('n_trajectories'))):
        # Each trajectory owns its randomized causal excitation parameters and all windows.
        family=['uniform','trapezoid','quartic'][j%3]
        cfg={'case_id':f'kin_{j:03d}','trajectory_id':f'kin_{j:03d}',
             'family_id':f'kinematic_oscillation_{j:03d}',
             'waveform_family':'analytic_oscillation','pressure_family':family,
             'a':float(rng.uniform(2,8)),'Fz':float(rng.uniform(2500,5500)),
             'amplitude_x':float(rng.uniform(.06,.7)),'amplitude_y':float(rng.uniform(-.4,.4)),
             'frequency':float(rng.uniform(12,30)),'phase':float(rng.uniform(0,2*np.pi))}
        split='train' if j<16 else ('validation' if j<20 else 'test')
        cfg['split']=split
        def boundary(t):
            return [cfg['amplitude_x']*(.7+np.sin(cfg['frequency']*t+cfg['phase'])),
                    cfg['amplitude_y']*np.cos(.7*cfg['frequency']*t)],cfg['a'],cfg['Fz']
        initial=s.steady_state(boundary(0)[0],cfg['a'])
        rf=s.simulate(t,boundary,initial,family)
        refined=fine.simulate(tf,boundary,fine.steady_state(boundary(0)[0],cfg['a']),family)
        ef=float(np.max(np.linalg.norm(rf['force']-refined['force'][::2],axis=1))/cfg['Fz'])
        ez=float(np.sqrt(np.mean((rf['z']-refined['z'][::2,::2])**2))/(p.mu_s/min(p.sigma0)))
        if ef>=value('force_gate') or ez>=value('state_gate'):raise RuntimeError(f'Refinement gate failed: {j}, {ef}, {ez}')
        flags={'case_id':cfg['case_id'],'split':split,'max_force_error_over_Fz':ef,'normalized_state_RMS':ez,
               'clamp_events':0,'out_of_domain':False,'quality':'verified_reference','scope':'G0/G1 numerical pilot'}
        records.append(flags);configs.append(cfg);forces.append(rf['force']);fields.append(rf['z']);moments.append(rf['Mz'])
        slips.append([boundary(q)[0] for q in t]);speeds.append(cfg['a']);loads.append(cfg['Fz']);shapes.append(family)
        groups.append(cfg['trajectory_id']);splits.append(split)
    arrays=dict(t=t,grid_m=s.x,integration_weights=s.weights,z=np.asarray(fields),force=np.asarray(forces),Mz=np.asarray(moments),
                vr=np.asarray(slips),transport_speed=np.asarray(speeds),Fz=np.asarray(loads),pressure_family=np.asarray(shapes),
                trajectory_id=np.asarray(groups),split=np.asarray(splits),parameter_set_id=np.asarray('deur2002_normalized_design_interface'),
                solver_version=np.asarray(VERSION))
    np.savez_compressed(ROOT/'pilot_reference.npz',**arrays)
    (DATA/'kinematic_configs.json').write_text(json.dumps(configs,indent=2),encoding='utf-8')
    # Single-wheel candidate examples: same z0/omega0 is copied for each command.
    samples=[];z0s=[];z1s=[];outforces=[];impulses=[];omegas=[];brakes=[]
    for j in range(int(value('n_wheel_trajectories'))):
        vx=float(rng.uniform(5,12));vy=float(rng.uniform(-.4,.4));fz=float(rng.uniform(2500,5000))
        family=['uniform','trapezoid','quartic'][j%3]
        boundary=HeldBoundary(vx,vy,fz,family);w=WheelState(vx/p.r,0)
        z=s.steady_state([0,vy],vx);zf=fine.steady_state([0,vy],vx)
        split='train' if j<8 else ('validation' if j<10 else 'test')
        for command in [0.,200.,500.]:
            rr=reference_step(s,z,w,command,boundary,value('horizon'),dt)
            ff=reference_step(fine,zf,w,command,boundary,value('horizon'),dt/2)
            ef=float(np.max(np.linalg.norm(rr['force']-ff['force'][::2],axis=1))/fz)
            if ef>=value('force_gate'):raise RuntimeError('Candidate dataset refinement failed')
            samples.append({'case_id':f'wheel_{j:03d}_cmd_{int(command)}','trajectory_id':f'wheel_{j:03d}',
                'family_id':f'wheel_snapshot_{j:03d}','split':split,'Vx':vx,'Vy':vy,'Fz':fz,
                'pressure_family':family,'omega0':w.omega,'brake_torque0':w.brake_torque,'candidate_brake_torque':command,
                't0':0.,'dt_control':value('dt_control'),'horizon':value('horizon'),
                'forecast_model':'held_boundary_first_order_rate_limited_actuator',
                'max_force_error_over_Fz':ef,'quality':'verified_reference','clamp_events':0,'out_of_domain':False})
            z0s.append(z);z1s.append(rr['next_tire_state']);outforces.append(rr['force']);impulses.append(rr['force_impulse'])
            omegas.append(rr['omega']);brakes.append(rr['brake_torque'])
    np.savez_compressed(DATA/'candidate_reference.npz',tau_queries=rr['t'],grid_m=s.x,integration_weights=s.weights,
        z0=np.asarray(z0s),z_next=np.asarray(z1s),force=np.asarray(outforces),omega=np.asarray(omegas),
        applied_brake_torque=np.asarray(brakes),force_impulse=np.asarray(impulses),
        split=np.asarray([q['split'] for q in samples]),trajectory_id=np.asarray([q['trajectory_id'] for q in samples]),
        metadata_json=np.asarray(json.dumps(samples)),solver_version=np.asarray(VERSION))
    (DATA/'candidate_metadata.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
    (DATA/'quality_checks.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    files=[ROOT/'pilot_reference.npz',DATA/'candidate_reference.npz',DATA/'kinematic_configs.json',DATA/'candidate_metadata.json',DATA/'quality_checks.json']
    manifest={'schema_version':'1.0','generated_local_date':'2026-10-03','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'seed':int(value('seed')),'solver_version':VERSION,'dtype':'float64','parameter_registry_sha256':sha(ROOT/'parameter_registry.csv'),
              'model_spec_sha256':sha(ROOT/'model_spec.md'),'solver_sha256':sha(ROOT/'reference_solver.py'),
              'code_sha256':{name:sha(ROOT/name) for name in ['parameters.py','pressure.py','wheel_interface.py','generate_reference.py']},
              'python':platform.python_version(),'numpy':np.__version__,'platform':platform.platform(),
              'nx':nx,'dt_solver':dt,'kinematic_trajectories':len(records),'candidate_examples':len(samples),
              'quality':'verified_reference','qualification':'G0/G1 numerical only; no external review or experimental validation',
              'initialization':'analytic steady field; never reset per frame','split_policy':'group by trajectory before windowing; all candidate siblings same split',
              'future_information':'kinematic wave parameters must be predictor inputs; candidate data uses held causal boundary',
              'max_kinematic_refinement_error_over_Fz':max(x['max_force_error_over_Fz'] for x in records),
              'max_candidate_refinement_error_over_Fz':max(x['max_force_error_over_Fz'] for x in samples),
              'files':{str(f.relative_to(ROOT)):sha(f) for f in files}}
    (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ['kinematic_trajectories','candidate_examples','max_kinematic_refinement_error_over_Fz','max_candidate_refinement_error_over_Fz']},indent=2))

if __name__=='__main__':main()