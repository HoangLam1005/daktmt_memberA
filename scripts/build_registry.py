"""Rebuild the canonical, reviewed registry and JSON mirror from explicit source rows."""
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parent
S1="https://skoge.folk.ntnu.no/prost/proceedings/ifac2002/data/content/00284/284.pdf"
S2="https://dcsl.gatech.edu/papers/vsd04R.pdf"
rows=[]
def add(symbol,name,value,unit,lo,hi,status,source,notes,mode,module):
    rows.append(dict(symbol=symbol,name=name,value=value,unit=unit,min=lo,max=hi,
                     provenance=status,source=source,notes=notes,sampling=mode,module=module))

add('L','Contact length',.303,'m',.15,.4,'published',S1+' Appendix B','Literature tire; not measured robot','fixed','all')
add('Fz','Nominal wheel load',4000,'N',2000,6000,'published',S1+' Appendix B','Load sweeps are declared sensitivity','sampled','pressure,dataset')
add('L_sigma0_x','Original longitudinal stiffness product',314000,'N','','','published',S1+' Appendix B','Preserve original L*sigma0 convention','fixed','conversion')
add('L_sigma0_y','Original lateral stiffness product',159200,'N','','','published',S1+' Appendix B','Preserve original L*sigma0 convention','fixed','conversion')
add('sigma0_x','Load-normalized longitudinal stiffness',314000/(.303*4000),'1/m',150,500,'derived',S1+' Eqs.1-3, Appendix B','L_sigma0_x/(L*Fz_nominal); frozen under load sweeps','fixed','PDE,force')
add('sigma0_y','Load-normalized lateral stiffness',159200/(.303*4000),'1/m',100,500,'derived',S1+' Eqs.1-3, Appendix B','L_sigma0_y/(L*Fz_nominal); frozen under load sweeps','fixed','PDE,force')
for sym in ['sigma1_x','sigma1_y']:
    add(sym,'Eulerian bristle damping',0,'s/m',0,.02,'published',S1+' Appendix B; '+S2+' Eq.2','Zero in base case; nonzero only in verification','fixed','force')
add('sigma2','Viscous coefficient',0,'s/m',0,.02,'published',S1+' Appendix B','Zero in base case','fixed','force')
for sym,name,v,unit,lo,hi in [('mu_k','Kinetic friction',.648,'1',.3,1.0),('mu_s','Static friction',1.671,'1',1,2),('v_s','Stribeck velocity',3.49,'m/s',1,6),('gamma','Stribeck exponent',.6,'1',.4,2)]:
    add(sym,name,v,unit,lo,hi,'published',S1+' Appendix B','Friction normalized by nominal Fz','fixed','PDE')
add('pressure_left','Trapezoid first breakpoint',.134,'1',.05,.3,'published',S1+' Appendix B','x_left/L','fixed','pressure')
add('pressure_right','Trapezoid second breakpoint',.707,'1',.6,.9,'published',S1+' Appendix B','x_right/L','fixed','pressure')
add('pressure_family','Selected normal load shape','trapezoid','category','','','design',S2+' Sec.4','Uniform/trapezoid/quartic; quartic=30*u^2*(1-u)^2 chosen here','sampled','pressure')
for sym,name,v,unit,lo,hi,notes,module in [
 ('r','Rolling radius',.3,'m',.1,.4,'Assumed interface radius; not from Appendix B','wheel'),
 ('Iw','Wheel rotational inertia',1.2,'kg*m^2',.1,2,'Assumed single-wheel bench inertia','wheel'),
 ('actuator_tau','Brake lag time constant',.02,'s',.01,.1,'Assumed first-order actuator','wheel'),
 ('brake_max','Maximum commanded brake torque',1200,'N*m',0,1200,'Physical actuator limit, not force clamp','wheel'),
 ('brake_rate','Maximum brake torque slew',10000,'N*m/s',1000,20000,'Physical actuator limit','wheel'),
 ('Vx','Longitudinal wheel-centre velocity',8,'m/s',2,20,'Forward only; literature reproduction uses 60 km/h','dataset'),
 ('Vy','Lateral wheel-centre velocity',.3,'m/s',-2,2,'Positive left; slip opposes Fy at equilibrium','dataset'),
 ('omega','Angular speed',26.666666666666668,'rad/s',0,80,'Positive forward rolling; reject reverse','wheel'),
 ('delta','Steering angle',0,'rad',-.5,.5,'Wheel-to-body rotation only; not solved tire input','vehicle interface'),
 ('v_slip_max','Sampled total slip speed ceiling',5,'m/s',0,5,'Dataset design, not physical law','dataset'),
 ('speed_epsilon','Slip-ratio reporting denominator floor',.1,'m/s',.01,.2,'Used for reported kappa only; never in PDE','interface'),
 ('nx','Reference grid nodes',257,'count',65,1025,'Includes both endpoints','solver'),
 ('dt_solver','Reference internal step',.001,'s',.000125,.004,'Pilot design; refine to check each family','solver'),
 ('dt_control','Control interval',.02,'s',.01,.05,'Assumed sample-and-hold command interval','wheel,dataset'),
 ('horizon','Single candidate horizon',.02,'s',.01,.05,'Default matches dt_control','wheel,dataset'),
 ('duration','Kinematic trajectory duration',.4,'s',.1,2,'Numerical pilot; not stopping-distance run','dataset'),
 ('seed','Random seed',20261003,'integer','','','Deterministic pilot sampling','dataset'),
 ('n_trajectories','Kinematic pilot trajectories',24,'count','','','16 train, 4 validation, 4 test groups','dataset'),
 ('n_wheel_trajectories','Candidate benchmark trajectories',12,'count','','','8 train, 2 validation, 2 test groups','dataset'),
 ('rtol','MOL BDF relative tolerance',1e-8,'1','','','Independent verification tolerance','independent'),
 ('atol','MOL BDF absolute state tolerance',1e-11,'m','','','Independent verification tolerance','independent'),
 ('force_gate','Fine/coarse maximum force error divided by Fz',.02,'1','','','Predetermined numerical acceptance; not ML accuracy guarantee','verification'),
 ('state_gate','RMS field error divided by mu_s/min(sigma0)',.03,'1','','','Predetermined numerical acceptance','verification'),
 ('rom_kappa_min','ROM closure search lower bound',.2,'1','','','Calibration on training excitations only','ROM'),
 ('rom_kappa_max','ROM closure search upper bound',5,'1','','','Calibration on training excitations only','ROM'),
 ('literature_speed','Deur reference speed',60/3.6,'m/s','','','60 km/h to SI','literature'),
 ('literature_angle','Deur Fig.4 slip-angle step',1,'degree','','','0 to 1 degree at t=0.05 s','literature')]:
    add(sym,name,v,unit,lo,hi,'design' if not sym.startswith('literature') else 'published',
        'model_spec.md design choice' if not sym.startswith('literature') else S1+' Fig.4 / Appendix B',notes,'fixed',module)

def main():
    with (ROOT/'parameter_registry.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (ROOT/'parameter_registry.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'{len(rows)} parameters written')
if __name__=='__main__': main()
