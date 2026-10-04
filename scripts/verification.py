"""Quantitative experiments, fixed acceptance gates, machine-readable evidence."""
from pathlib import Path
import csv,json,time,unittest
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize_scalar
from parameters import default_parameters,value
from pressure import line_load
from reference_solver import ReferenceSolver
from independent_solver import solve_mol
from rom import simulate_rom
from wheel_interface import reference_step,WheelState,HeldBoundary

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'

def write_csv(name,rows):
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run():
    OUT.mkdir(exist_ok=True)
    from reference_tests import ReferenceTests
    with (OUT/'unit_tests.log').open('w',encoding='utf-8') as f:
        result=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReferenceTests))
    if not result.wasSuccessful():raise RuntimeError('Unit tests failed; see results/unit_tests.log')
    p=default_parameters();Fz=value('Fz');metrics={'unit_tests':result.testsRun,'threshold_force_over_Fz':value('force_gate')}
    # Fixed dt, exact constant-input solution; refine space separately.
    rows=[];v=np.array([.18,.11]);a=4.;end=.2;dt=.0002
    for nx in [65,129,257,513]:
        s=ReferenceSolver(p,nx);z=s.zero_state()
        for _ in range(round(end/dt)):z=s.step(z,v,a,dt)        
        exact=s.steady_state(v,a)
        fe=s.outputs(exact,v,a,Fz)['force'];f=s.outputs(z,v,a,Fz)['force']
        rows.append({'nx':nx,'dx_m':s.x[1],'dt_s':dt,'state_rms_m':float(np.sqrt(np.mean((z-exact)**2))),
                     'force_error_over_Fz':float(np.linalg.norm(f-fe)/Fz)})
    write_csv('convergence_space.csv',rows)
    metrics['space_error_ratio_coarse_to_fine']=rows[0]['state_rms_m']/rows[-1]['state_rms_m']
    if not all(rows[j+1]['state_rms_m']<rows[j]['state_rms_m'] for j in range(3)):raise RuntimeError('Spatial convergence failed')
    # a=0 eliminates remapping error. DOP853 oracle independently computes local ODE.
    def smooth(t):return np.array([.25+.12*np.sin(27*t),.08*np.cos(17*t)]),0.,Fz
    def rhs(t,z):
        v,_,_=smooth(t);speed=np.linalg.norm(v)
        g=p.mu_k+(p.mu_s-p.mu_k)*np.exp(-(speed/p.v_s)**p.gamma)
        return v-p.sigma0*speed/g*z
    truth=solve_ivp(rhs,(0,.2),[0,0],method='DOP853',rtol=1e-12,atol=1e-14).y[:,-1]
    rows=[]
    for dt in [.004,.002,.001,.0005]:
        s=ReferenceSolver(p,3);r=s.simulate(np.linspace(0,.2,round(.2/dt)+1),smooth)
        rows.append({'dt_s':dt,'a_mps':0.,'state_error_m':float(np.linalg.norm(r['z'][-1,1]-truth))})
    write_csv('convergence_time.csv',rows)
    metrics['time_error_ratio_coarse_to_fine']=rows[0]['state_error_m']/rows[-1]['state_error_m']
    if not all(rows[j+1]['state_error_m']<rows[j]['state_error_m'] for j in range(3)):raise RuntimeError('Time convergence failed')
    # Independent MOL, smooth nonzero transport. Force integration explicitly repeated here.
    def moving(t):return np.array([.2+.1*np.sin(20*t),.12+.04*np.cos(13*t)]),4.,Fz
    rows=[]
    for nx in [65,129,257,513]:
        s=ReferenceSolver(p,nx)
        # Hold Courant number near 0.4 during refinement. A fixed dt can mask
        # agreement through cancellation of the two transport truncation errors.
        steps=int(np.ceil(.15/(.4*s.x[1]/4.)))
        times=np.linspace(0,.15,steps+1)
        ref=s.simulate(times,moving)
        other=solve_mol(p,s.x,times,moving)
        u=s.x/p.L
        raw=np.where(u<p.pressure_left,u/p.pressure_left,np.where(u<=p.pressure_right,1,(1-u)/(1-p.pressure_right)))
        q=raw*Fz/np.trapezoid(raw,s.x)
        fmol=-np.trapezoid(other*p.sigma0*q[None,:,None],s.x,axis=1)
        error=float(np.max(np.linalg.norm(fmol-ref['force'],axis=1))/Fz)
        rows.append({'nx':nx,'dt_moc_s':float(times[1]),'max_force_error_over_Fz':error,'state_rms_m':float(np.sqrt(np.mean((other-ref['z'])**2)))})
    write_csv('independent_comparison.csv',rows)
    metrics['independent_max_force_error_over_Fz']=rows[-1]['max_force_error_over_Fz']
    if rows[-1]['max_force_error_over_Fz']>=value('force_gate'):raise RuntimeError('Independent comparison failed')
    if not all(rows[j+1]['max_force_error_over_Fz']<rows[j]['max_force_error_over_Fz'] for j in range(3)):
        raise RuntimeError('Independent comparison must converge under joint refinement')
    # Pressure raw integral versus renormalized discrete load at multiple grids.
    rows=[]
    for nx in [65,129,257,513]:
        s=ReferenceSolver(p,nx)
        for family in ['uniform','trapezoid','quartic']:
            q,d=line_load(s.x,p.L,Fz,family)
            rows.append({'family':family,'nx':nx,**d,'minimum_N_per_m':float(q.min())})
    write_csv('pressure_normalization.csv',rows)
    metrics['max_discrete_load_error']=max(abs(r['load_relative_error']) for r in rows)
    # Sensitivity: one factor changed, same physical inputs.
    rows=[]
    for name in ['L','sigma0_x','sigma0_y','mu_s','mu_k','v_s','gamma']:
        for factor in [.8,1.,1.2]:
            pp=default_parameters(**{name:getattr(p,name)*factor});s=ReferenceSolver(pp,513)
            z=s.steady_state([.2,.1],4.)
            out=s.outputs(z,[.2,.1],4.,Fz)
            rows.append({'parameter':name,'factor':factor,'Fx_N':out['force'][0],'Fy_N':out['force'][1],'Mz_Nm':out['Mz']})
    write_csv('sensitivity.csv',rows)
    # Same present input, two initial histories. At t=0 slip is released, then memory is flushed.
    s=ReferenceSolver(p,257);times=np.linspace(0,.12,241);b=lambda t:([0.,0.],4.,Fz)
    za=s.steady_state([.2,.1],4.)
    hist=s.simulate(times,b,za);empty=s.simulate(times,b)
    np.savez_compressed(OUT/'memory_ablation.npz',t=times,force_history=hist['force'],force_zero=empty['force'],z0_history=za)
    metrics['history_initial_force_difference_N']=float(np.linalg.norm(hist['force'][0]))
    # ROM calibration uses only fixed training trajectories, evaluation uses held-out cases.
    train=[];test=[]
    for j,(amp,freq) in enumerate([(.12,12),(.25,18),(.45,23),(.18,31),(.32,37)]):
        boundary=lambda t,amp=amp,freq=freq: (np.array([amp*(1+.4*np.sin(freq*t)),.1*np.cos(freq*.7*t)]),4.,Fz)
        data=s.simulate(times,boundary)
        (train if j<3 else test).append((boundary,data))
    def objective(k):return float(np.mean([np.mean((simulate_rom(p,times,b,k)['force']-r['force'])**2)/Fz**2 for b,r in train]))
    fit=minimize_scalar(objective,bounds=(value('rom_kappa_min'),value('rom_kappa_max')),method='bounded')
    if not fit.success:raise RuntimeError('ROM calibration failed')
    k=float(fit.x);scores=[]
    for j,(b,r) in enumerate(test):
        started=time.perf_counter();rr=simulate_rom(p,times,b,k);romtime=time.perf_counter()-started
        started=time.perf_counter();s.simulate(times,b);reftime=time.perf_counter()-started
        scores.append({'case':j,'force_RMSE_N':float(np.sqrt(np.mean((rr['force']-r['force'])**2))),
                       'max_error_over_Fz':float(np.max(np.linalg.norm(rr['force']-r['force'],axis=1))/Fz),
                       'REF_wall_s':reftime,'ROM_wall_s':romtime})
    write_csv('rom_evaluation.csv',scores)
    (ROOT/'rom_calibration.json').write_text(json.dumps({'kappa':k,'objective_train_MSE_over_Fz2':fit.fun,
        'training_cases':3,'heldout_cases':2,'target_pressure':'trapezoid','not_MCU_benchmark':True},indent=2))
    # Wheel horizon step refinement, including force impulse.
    b=HeldBoundary(8,.3,Fz);w=WheelState(8/p.r)
    fine=ReferenceSolver(p,1025);truth=reference_step(fine,fine.zero_state(),w,500,b,.04,.000125)
    rows=[]
    for nx,dt in [(129,.002),(257,.001),(513,.0005)]:
        ss=ReferenceSolver(p,nx);r=reference_step(ss,ss.zero_state(),w,500,b,.04,dt)
        rows.append({'nx':nx,'dt_s':dt,'force_error_over_Fz':float(np.linalg.norm(r['force'][-1]-truth['force'][-1])/Fz),
                     'omega_error_rad_s':abs(r['omega'][-1]-truth['omega'][-1]),
                     'impulse_error_Ns':float(np.linalg.norm(r['force_impulse']-truth['force_impulse']))})
    write_csv('wheel_convergence.csv',rows)
    if rows[-1]['force_error_over_Fz']>=value('force_gate'):raise RuntimeError('Wheel convergence gate failed')
    metrics['G0']='PASS documented numerical model'
    metrics['G1']='PASS tested cases only; Member D review pending'
    metrics['G2']='PARTIAL: source conditions reconstructed; no digitized published-curve error'
    metrics['G3']='NOT_AVAILABLE: no tire measurements'
    (OUT/'verification_metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print(json.dumps(metrics,indent=2))
    return metrics

if __name__=='__main__':run()