"""Float64 semi-Lagrangian MoC reference. See model_spec.md A1--A9.

Inputs to step are held throughout that step. No hidden force/state clamps.
"""
import numpy as np
from pressure import line_load, quadrature_weights

VERSION = "A-moc-1.0.0"

def coefficients(vr, p):
    vr = np.asarray(vr, dtype=float)
    if vr.shape != (2,) or not np.isfinite(vr).all():
        raise ValueError("vr must be a finite 2-vector in m/s")
    speed = np.linalg.norm(vr)
    g = p.mu_k+(p.mu_s-p.mu_k)*np.exp(-(speed/p.v_s)**p.gamma)
    return float(g), p.sigma0*speed/g

def reaction(z, vr, C, elapsed):
    """Stable exponential update, including C=0 without division by zero."""
    elapsed = np.asarray(elapsed, dtype=float)
    q = elapsed[..., None]*C
    phi = np.ones_like(q)
    np.divide(-np.expm1(-q), q, out=phi, where=q != 0)
    return z*np.exp(-q)+vr*elapsed[..., None]*phi

class ReferenceSolver:
    def __init__(self, parameters, nx=257):
        self.p = parameters.validate()
        if int(nx) != nx or nx < 3:
            raise ValueError("nx must be an integer >=3")
        self.x = np.linspace(0., self.p.L, int(nx))
        self.weights = quadrature_weights(self.x)

    def zero_state(self):
        return np.zeros((len(self.x),2), dtype=np.float64)

    def validate_state(self, z):
        z = np.asarray(z, dtype=float)
        if z.shape != (len(self.x),2) or not np.isfinite(z).all():
            raise ValueError("State must have shape (nx,2), finite and in metres")
        return z

    def step(self, z, vr, a, dt):
        z = self.validate_state(z)
        if not np.isfinite([a, dt]).all() or a < 0 or dt <= 0:
            raise ValueError("Require a >= 0, dt > 0 and forward contact orientation")
        vr = np.asarray(vr, dtype=float)
        _, C = coefficients(vr, self.p)
        if a == 0:
            # No inflow boundary in a stationary patch. Do not zero the first node.
            return reaction(z, vr, C, dt)
        foot = self.x-a*dt
        zfoot = np.column_stack([np.interp(foot, self.x, z[:,i], left=0) for i in range(2)])
        residence = np.minimum(dt, self.x/a)
        out = reaction(zfoot, vr, C, residence)
        out[0] = 0.0
        if not np.isfinite(out).all():
            raise FloatingPointError("Nonfinite MoC state")
        return out

    def steady_state(self, vr, a):
        if not np.isfinite(a) or a < 0:
            raise ValueError("Require finite a >= 0")
        vr = np.asarray(vr, dtype=float)
        _, C = coefficients(vr, self.p)
        if a == 0:
            if np.linalg.norm(vr) == 0:
                return self.zero_state()  # selected member of nonunique equilibria
            return np.broadcast_to(vr/C, self.zero_state().shape).copy()
        return reaction(self.zero_state(), vr, C, self.x/a)

    def outputs(self, z, vr, a, Fz, family="trapezoid"):
        z = self.validate_state(z)
        if not np.isfinite(a) or a < 0:
            raise ValueError("Require finite a >= 0")
        vr = np.asarray(vr, dtype=float)
        _, C = coefficients(vr, self.p)
        dzdt = vr-C*z
        if a > 0:
            dzdt = dzdt-a*np.gradient(z, self.x, axis=0, edge_order=2)
            dzdt[0] = 0.0  # fixed Eulerian boundary value for positive a
        q, diag = line_load(self.x,self.p.L,Fz,family,self.p.pressure_left,self.p.pressure_right)
        mu = -(self.p.sigma0*z+self.p.sigma1*dzdt+self.p.sigma2*vr)
        traction = q[:,None]*mu
        force = self.weights@traction
        moment = self.weights@((self.p.L/2-self.x)*traction[:,1])
        return {"force":force, "Mz":float(moment), "normal_line_load":q,
                "traction_line_load":traction, "partial_t_z":dzdt, "pressure_diagnostics":diag}

    def simulate(self, times, boundary, z0=None, family="trapezoid"):
        """boundary(t) -> (vr[2], transport_speed, Fz), midpoint frozen per interval."""
        times = np.asarray(times,dtype=float)
        if times.ndim != 1 or len(times)<2 or not np.isfinite(times).all() or np.any(np.diff(times)<=0):
            raise ValueError("Times must be finite, strictly increasing")
        z = self.zero_state() if z0 is None else self.validate_state(z0).copy()
        fields, forces, moments = [z.copy()], [], []
        for k,t in enumerate(times):
            if k:
                vr,a,_ = boundary((times[k-1]+t)/2)
                z = self.step(z,vr,a,t-times[k-1])
                fields.append(z.copy())
            vr,a,Fz = boundary(t)
            out = self.outputs(z,vr,a,Fz,family)
            forces.append(out["force"]); moments.append(out["Mz"])
        return {"t":times,"x":self.x.copy(),"z":np.asarray(fields),
                "force":np.asarray(forces),"Mz":np.asarray(moments)}