## III-A. Physics reference and causal state transition

The reference state transition directly integrates the characteristics of Eq. (A4). Under a frozen-step input assumption over time step $\Delta t$, each characteristic curve $dx/dt = a(t)$ travels across the contact patch at transport speed $a(t) = |\omega r|$ and carries the linear reaction:
$$\dot{z}_i + C_i z_i = v_{ri}, \quad i \in \{x, y\}$$
Equation (A9) evaluates this reaction along the characteristic curve using an exact integrating-factor exponential state transition:
$$z_i^{n+1}(x) = z_i^n(x - a \Delta t) \, e^{-C_i \Delta t} + \frac{v_{ri}}{C_i} \left(1 - e^{-C_i \Delta t}\right)$$
For interior grid points $x \ge a \Delta t$, the characteristic foot $x - a \Delta t$ is interpolated onto the spatial mesh of the preceding time step. A characteristic entering the patch during the step ($x < a \Delta t$) originates from the inflow boundary condition ($z_i(0, t^*) = 0$) and is integrated strictly over its physical residence time $\tau = x / a$:
$$z_i^{n+1}(x) = \frac{v_{ri}}{C_i} \left(1 - e^{-C_i (x / a)}\right)$$
In the singular limit $C_i \to 0$, the update is evaluated continuously and stably using the numerical identity $\frac{1 - e^{-u}}{u} = -\frac{\operatorname{expm1}(-u)}{u}$, eliminating artificial numerical clipping of bristle states or forces.

For smooth prescribed continuous trajectories, kinematic inputs are evaluated at the temporal midpoint of each step ($t_{n+1/2} = t_n + \Delta t / 2$). The temporal midpoint approximation and spatial remapping errors are audited independently. Although the reaction subproblem admits an exact analytical update along characteristics, the spatial remapping introduces bounded numerical diffusion. Normal line loads $p(x)$ are normalized using the identical discrete quadrature weights (composite Simpson's or trapezoidal rule) as the macroscopic force integral, and the uncorrected quadrature discrepancy is recorded in the verification metrics.

In candidate braking evaluation, the causal boundary conditions comprise the current wheel-center longitudinal and lateral velocities $\mathbf{V}_w = [V_x, V_y]^T$, vertical contact load $F_z$, normal pressure parameters, tire constitutive parameters, and actuator braking torque $T_b$. These boundary values are held constant over the local candidate evaluation horizon. Wheel angular speed $\omega$ and the distributed bristle state field $\mathbf{z}(x, t)$ evolve dynamically and concurrently via:
$$I_w \dot{\omega} = -T_b - r F_x$$
Each evaluated candidate receives an isolated, independent deep copy of the current state profile. The physics reference returns discrete force time histories, total force impulse, and the terminal wheel and tire state vectors. Wheel-lock events ($\omega \le 0$) lie outside the valid operational domain of this contact solver and immediately raise a dedicated termination exception.

The reduced-order model (ROM) retains two lumped dynamic state averages $\bar{z}_x(t), \bar{z}_y(t)$ subject to an empirical convective loss term $\kappa a / L$:
$$\dot{\bar{z}}_i = v_{ri} - C_i \bar{z}_i - \kappa \frac{a}{L} \bar{z}_i, \quad i \in \{x, y\}$$
The closure parameter $\kappa$ is calibrated solely on designated training trajectories; held-out scenarios are reserved exclusively for objective evaluation. The lumped ROM serves as a computational surrogate, not an exact equivalent of the distributed field. Normal pressure and dynamic memory ablation benchmarks apply identical current inputs and normal loads to strictly isolate constitutive effects.

The delivered pilot suite incorporates both open-loop prescribed kinematic trajectories and closed-loop causal braking candidates. In prescribed trajectories, the motion profile must be explicitly supplied to downstream predictors. Neither interface leaks non-causal future plant information to candidate controllers. Numerical algorithmic verification and physical real-world validation remain strictly delineated claims.
