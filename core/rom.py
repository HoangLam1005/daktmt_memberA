"""Two-state dynamic ROM with calibrated convective loss; no moment claim."""
import numpy as np
from reference_solver import coefficients, reaction

def simulate_rom(p,times,boundary,kappa,z0=None):
    if not np.isfinite(kappa) or kappa<=0:
        raise ValueError('Positive closure coefficient required')
    z=np.zeros(2) if z0 is None else np.array(z0,dtype=float,copy=True)
    forces=[];states=[]
    for j,t in enumerate(times):
        if j:
            v,a,_=boundary((times[j-1]+t)/2)
            _,C=coefficients(v,p)
            z=reaction(z,np.asarray(v),C+kappa*a/p.L,t-times[j-1])
        v,a,Fz=boundary(t);_,C=coefficients(v,p)
        rate=np.asarray(v)-(C+kappa*a/p.L)*z
        forces.append(-Fz*(p.sigma0*z+p.sigma1*rate+p.sigma2*np.asarray(v)))
        states.append(z.copy())
    return {'force':np.asarray(forces),'z':np.asarray(states)}
