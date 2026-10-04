"""Causal, nonmutating candidate prediction for one forward wheel.

Midpoint coupling; held Vx,Vy,Fz and pressure during the horizon.
Stops/reverse require a vehicle-level contact/locking model and are rejected.
"""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class WheelState:
    omega: float
    brake_torque: float=0.0

@dataclass(frozen=True)
class HeldBoundary:
    Vx: float
    Vy: float
    Fz: float
    pressure_family: str="trapezoid"

def wheel_to_body(force, delta):
    c,s=np.cos(delta),np.sin(delta)
    return np.array([[c,-s],[s,c]])@np.asarray(force)

def wheel_velocity(Vx_body,Vy_body,yaw_rate,wheel_x,wheel_y,delta):
    return wheel_to_body([Vx_body-yaw_rate*wheel_y,Vy_body+yaw_rate*wheel_x],-delta)

def reference_step(solver, tire_state, wheel_state, candidate_command, boundary,
                   horizon, dt_solver=.001):
    p=solver.p
    if not np.isfinite([boundary.Vx,boundary.Vy,boundary.Fz,wheel_state.omega,
                        wheel_state.brake_torque,candidate_command,horizon,dt_solver]).all():
        raise ValueError('All inputs must be finite')
    if min(boundary.Vx,boundary.Fz,wheel_state.omega,horizon,dt_solver)<=0:
        raise ValueError('Requires forward wheel, positive contact load, horizon and step')
    if not 0<=candidate_command<=p.brake_max or not 0<=wheel_state.brake_torque<=p.brake_max:
        raise ValueError('Command or actuator outside physical bounds')
    z=solver.validate_state(tire_state).copy()
    omega=float(wheel_state.omega); brake=float(wheel_state.brake_torque)
    # Resolve actuator lag even when caller requests an excessively large step.
    n=max(int(np.ceil(horizon/dt_solver)),int(np.ceil(horizon/(.25*p.actuator_tau))))
    h=horizon/n
    times=np.linspace(0,horizon,n+1); forces=[]; moments=[]; speeds=[omega]; brakes=[brake]
    impulse=np.zeros(2)
    def output(field,om):
        return solver.outputs(field,[boundary.Vx-p.r*om,boundary.Vy],p.r*om,boundary.Fz,boundary.pressure_family)
    first=output(z,omega); forces.append(first['force']);moments.append(first['Mz'])
    for _ in range(n):
        rate=np.clip((candidate_command-brake)/p.actuator_tau,-p.brake_rate,p.brake_rate)
        bmid=brake+.5*h*rate
        bnext=brake+h*np.clip((candidate_command-bmid)/p.actuator_tau,-p.brake_rate,p.brake_rate)
        f0=output(z,omega)['force']
        omid=omega+.5*h*(-bmid-p.r*f0[0])/p.Iw
        if omid<=0:
            raise ValueError('wheel_stop_event: reduce horizon or use Member C locking model')
        zmid=solver.step(z,[boundary.Vx-p.r*omega,boundary.Vy],p.r*omega,h/2)
        fmid=output(zmid,omid)['force']
        onext=omega+h*(-bmid-p.r*fmid[0])/p.Iw
        if onext<=0:
            raise ValueError('wheel_stop_event: no silent omega clamp')
        z=solver.step(z,[boundary.Vx-p.r*omid,boundary.Vy],p.r*omid,h)
        omega,brake=onext,bnext
        out=output(z,omega);forces.append(out['force']);moments.append(out['Mz'])
        speeds.append(omega);brakes.append(brake);impulse+=h*fmid
    return {'t':times,'force':np.asarray(forces),'Mz':np.asarray(moments),
            'omega':np.asarray(speeds),'brake_torque':np.asarray(brakes),
            'next_tire_state':z,'next_wheel_state':WheelState(omega,brake),
            'force_impulse':impulse,'diagnostics':{'clamp_events':0,'out_of_domain':False,
            'forecast':'held_boundary','wheel_integrator':'explicit_midpoint','dt_solver':h}}
