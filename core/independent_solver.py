"""Independent first-order upwind MOL + SciPy BDF.

Deliberately does not import reference_solver, its coefficients or reaction.
Shares only parameter values and prescribed inputs, not the update algorithm.
"""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import lil_matrix

def solve_mol(p, x, times, boundary, z0=None, rtol=1e-8, atol=1e-11):
    n = len(x)
    dx = np.diff(x)
    if not np.allclose(dx,dx[0]):
        raise ValueError("Independent verifier uses uniform grid")
    initial = np.zeros((n,2)) if z0 is None else np.array(z0,dtype=float,copy=True)
    def rhs(t,y):
        v,a,_ = boundary(t)
        v=np.asarray(v)
        s=np.sqrt(v[0]*v[0]+v[1]*v[1])
        g=p.mu_k+(p.mu_s-p.mu_k)*np.exp(-(s/p.v_s)**p.gamma)
        z=y.reshape(n,2)
        result=v-z*np.array([p.sigma0_x,p.sigma0_y])*s/g
        if a>0:
            result[1:] -= a*(z[1:]-z[:-1])/dx[0]
            result[0]=0
        return result.ravel()
    sparsity=lil_matrix((2*n,2*n),dtype=int)
    for j in range(2*n):
        sparsity[j,j]=1
        if j>=2: sparsity[j,j-2]=1
    result=solve_ivp(rhs,(times[0],times[-1]),initial.ravel(),t_eval=times,
                     method="BDF",rtol=rtol,atol=atol,jac_sparsity=sparsity.tocsr())
    if not result.success:
        raise RuntimeError(result.message)
    return result.y.T.reshape(len(times),n,2)
