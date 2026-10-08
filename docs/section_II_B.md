# II-B. Contact Load, Distributed LuGre Dynamics, and Tire-Force Interface

We model each tire contact patch with a one-dimensional longitudinal coordinate and two tangential bristle-memory states. The purpose of this section is to define the **paper-facing tire model and interface** used by the reference solver, predictor, and vehicle plant. The model is a numerical reference representation of distributed tire friction; it is not a validated pressure map or an identified tire model for a specific commercial robot.

**Canonical notation and provenance.** Use [`parameter_manifest.md`](parameter_manifest.md) as the working source of truth for the selected contact-patch length, load-shape ID, LuGre constitutive parameters, source versions, units, and closure state. Values imported from literature retain their original definitions or an explicit dimensional mapping. Unresolved quantities remain **[open_item]** rather than being inferred from unrelated robot dimensions.

**Interface with II-A.** This section returns the signed wheel-frame quantities $(F_x^w,F_y^w,M_z)$ used by II-A.2–II-A.4. The contact-patch length is denoted $L_c$ to avoid collision with the vehicle wheelbase $L_{wb}$ in II-A.

## II-B.1. Contact-Patch Coordinate, Wheel Frame, and Relative Slip

The contact coordinate increases from the leading edge to the trailing edge,

$$
\zeta \in [0,L_c].
$$

The distributed bristle-deformation state is

$$
\mathbf z(\zeta,t)
=
\begin{bmatrix}
z_x(\zeta,t)\\
z_y(\zeta,t)
\end{bmatrix},
$$

where $z_x$ and $z_y$ are the longitudinal and lateral internal deformation states.

The wheel-frame axes follow the interface used in II-A: $+x_w$ is forward along the wheel plane, $+y_w$ is leftward, and $+z_w$ is upward. The tire-force outputs are the road-on-wheel reactions in this frame.

II-A supplies the Cartesian wheel-center velocity $(v_x^w,v_y^w)$ and wheel speed $\omega$. The project relative-slip convention is

$$
\mathbf v_r
=
\begin{bmatrix}
v_{rx}\\
v_{ry}
\end{bmatrix}
=
\begin{bmatrix}
v_x^w-r_w\omega\\
v_y^w
\end{bmatrix},
$$

with slip-speed magnitude

$$
s=\|\mathbf v_r\|_2=\sqrt{v_{rx}^2+v_{ry}^2}.
$$

**Why Cartesian wheel-frame slip is used.** II-A already computes $(v_x^w,v_y^w)$ directly from rigid-body kinematics. Reusing that pair avoids an unnecessary polar conversion and keeps the tire interface well defined in the low-speed regime where a slip angle becomes numerically awkward.

**Sign-interface requirement.** In forward braking, $v_{rx}>0$ is possible under the adopted project convention while the road-on-wheel longitudinal force is normally $F_x^w<0$. The source-paper sign convention and the project sign convention must therefore be connected by an explicit mapping and verified by pure-traction, pure-braking, and lateral-slip tests. Do not infer force sign from slip sign alone.

## II-B.2. Physical Pressure and One-Dimensional Normal Line Load

A physical two-dimensional contact pressure, if available, is denoted

$$
p(\zeta,y)\quad[\mathrm{Pa}].
$$

The one-dimensional model uses the corresponding normal line load

$$
q(\zeta)=\int p(\zeta,y)\,dy,
$$

with units

$$
q(\zeta)\quad[\mathrm{N/m}].
$$

The total vertical wheel load is

$$
\int_0^{L_c}q(\zeta)\,d\zeta=F_z,
$$

with the admissibility condition

$$
q(\zeta)\ge0.
$$

**Why $q$ is kept distinct from $p$.** The current distributed model resolves one spatial coordinate along the contact patch. If no measured two-dimensional pressure map is available, the paper must describe the numerical input as a **normal line load**, not as a measured pressure field. This follows the project data-provenance rule: a missing contact width or sensor channel is not reconstructed and relabeled as measured data.

For a source-backed dimensionless shape function $w$, the normalized line load may be written as

$$
q(\zeta)
=
F_z
\frac{w(\zeta/L_c)}
{\displaystyle\int_0^{L_c}w(\xi/L_c)\,d\xi}.
$$

This normalization preserves the same $F_z$ while changing the spatial distribution.

## II-B.2.1. Load-Shape Families Used in Controlled Comparisons

The current study supports three literature-backed families:

1. **Uniform:** baseline distribution with constant load along the patch.
2. **Trapezoidal:** nonuniform distribution with piecewise-linear entry/exit regions.
3. **Quartic:** higher-order nonuniform family used only when the complete source-specific coefficients and admissibility conditions are supplied.

For the uniform baseline,

$$
w_{unif}(s)=1,\qquad 0\le s\le1.
$$

A convenient normalized trapezoidal family is

$$
w_{trap}(s)=
\begin{cases}
\dfrac{s}{\alpha}, & 0\le s\le\alpha,\\[6pt]
1, & \alpha\le s\le\beta,\\[6pt]
\dfrac{1-s}{1-\beta}, & \beta\le s\le1,
\end{cases}
$$

with

$$
0<\alpha\le\beta<1.
$$

The quartic family is not assigned a new project-specific formula here. It is used only with a complete source-backed parameterization **[published_reference]**; otherwise its coefficients remain **[open_item]**.

**Why uniform, trapezoidal, and quartic are separated.** Uniform loading is the simplest matched-total-load baseline. Trapezoidal loading introduces controlled nonuniformity without inventing a new pressure law. Quartic loading is reserved as a source-supported higher-order sensitivity case. None of these families is claimed to be the measured pressure distribution of the representative robot without independent pressure data [Deur2002; Tsiotras2004].

**Controlled comparison rule.** Pressure-shape ablations must hold total normal load fixed:

$$
\int_0^{L_c}q_1(\zeta)\,d\zeta
=
\int_0^{L_c}q_2(\zeta)\,d\zeta
=
F_z.
$$

Changing both $F_z$ and the shape in the same ablation would confound total-load and spatial-distribution effects.

## II-B.3. Distributed LuGre State Dynamics

For each tangential direction $i\in\{x,y\}$, the selected distributed LuGre reference equation is

$$
\frac{\partial z_i}{\partial t}
+
a(t)\frac{\partial z_i}{\partial\zeta}
=
v_{ri}(t)-C_i(t)z_i,
$$

where the forward transport speed is

$$
a(t)=|\omega(t)r_w|.
$$

The coefficient $C_i(t)$ follows the selected LuGre constitutive convention and current slip state. The longitudinal and lateral channels are not treated as two unrelated scalar friction laws; they retain the coupling defined by the selected constitutive model and its common slip-speed dependence [Tsiotras2004].

**Why the full distributed state is retained.** Two trajectories can have the same instantaneous wheel kinematics but different prior bristle-deformation fields. Retaining $\mathbf z(\zeta,t)$ therefore preserves transient friction memory that would be discarded by a purely static slip-to-force map.

**Model-integrity rule.** No extra friction-circle correction, undocumented clipping of $\mathbf z$, or post-integration force saturation is inserted and then presented as part of the original distributed LuGre law. Any added limiter must be identified as a separate project model component and logged.

## II-B.4. Initial, Inflow, and Zero-Transport Conditions

For forward rolling with $a(t)>0$, the leading-edge inflow condition is

$$
\mathbf z(0,t)=\mathbf0.
$$

The initial field

$$
\mathbf z(\zeta,0)
$$

must come from a documented warm-up, a known valid solution, or an inherited state from the same trajectory.

**Why the memory field is not reset each sample.** Resetting $\mathbf z$ to zero at every controller or predictor call would remove the transient state that motivates the distributed model. Candidate evaluations may deep-copy the current field, but they must not reinitialize it.

When

$$
a(t)=0,
$$

the transport term vanishes and the PDE reduces locally to the corresponding reaction ODE. No division by $a$ or artificial inflow condition is introduced in this limit.

**Reverse and contact-loss boundary.** Reverse rolling changes the inflow edge; loss of contact invalidates the positive-load contact model. Both remain outside the baseline reference domain until separate event/boundary handling is specified and verified. This matches II-A's `wheel_lock`, `OOD_OMEGA`, and contact-loss domain rules rather than silently extending the tire law.

## II-B.5. Local Tangential Response and Macroscopic Tire Outputs

Let the local normalized tangential response be

$$
\boldsymbol\mu(\zeta,t)
=
\begin{bmatrix}
\mu_x(\zeta,t)\\
\mu_y(\zeta,t)
\end{bmatrix}.
$$

The wheel-frame tire forces are

$$
F_x^w
=
\int_0^{L_c}\mu_x(\zeta,t)\,q(\zeta)\,d\zeta,
$$

$$
F_y^w
=
\int_0^{L_c}\mu_y(\zeta,t)\,q(\zeta)\,d\zeta.
$$

The self-aligning moment about the contact-patch center is

$$
M_z
=
\int_0^{L_c}
\left(
\frac{L_c}{2}-\zeta
\right)
\mu_y(\zeta,t)\,q(\zeta)\,d\zeta.
$$

These are the signed outputs delivered to II-A. II-A rotates $(F_x^w,F_y^w)$ once into the vehicle body frame; the wheel-spin equation continues to use the wheel-frame longitudinal force.

**Why $M_z$ is retained.** The vehicle yaw equation in II-A includes the tire self-aligning moment. Omitting $M_z$ in a turning evaluation changes the plant interface and therefore requires a separately versioned alternative model rather than an undocumented omission.

## II-B.6. Where the Load Distribution Enters the Selected LuGre Model

For the selected formulation, $q(\zeta)$ does **not** appear directly in the state PDE.

Under prescribed kinematics, if $\mathbf v_r$, $a$, the constitutive parameters, and the initial/boundary state are held fixed, changing only $q(\zeta)$ does not directly change

$$
\mathbf z(\zeta,t).
$$

Instead, the direct path is

$$
q(\zeta)
\longrightarrow
\text{spatial weighting}
\longrightarrow
F_x^w,\ F_y^w,\ M_z.
$$

**Why this distinction matters.** A pressure-shape experiment under prescribed motion tests the direct weighting effect. In the coupled plant, however, a changed $F_x^w$ alters the wheel rotational dynamics, which changes $\omega$, slip, and later $\mathbf z$. The model therefore has an indirect pressure-to-memory path only after tire force is coupled back into wheel/vehicle dynamics.

## II-B.7. Coupling to Wheel Dynamics and Candidate Prediction

For the braking-only interface used in II-A,

$$
J_w\dot\omega
=
-T_b^{applied}
-r_wF_x^w,
$$

when drive torque is zero.

A candidate brake request changes applied torque through the actuator model, then changes $\omega$, relative slip, the distributed bristle state, and the tire outputs.

**Why future wheel speed is not supplied.** Candidate evaluation is a causal prediction problem. The realized future $\omega$ from the plant trajectory would leak the answer into the predictor. Each candidate instead starts from the same current state and propagates its own wheel/tire trajectory.

**Candidate-state isolation.** Every candidate receives an independent copy of the current $(\omega,\mathbf z)$ state. Only the command actually selected and applied is allowed to advance the operating state.

## II-B.8. Modeling Scope, Provenance, and Claim Boundary

The baseline model is one-dimensional in contact geometry and two-component in tangential deformation. The current scope excludes strong spin/camber effects, two-dimensional transverse pressure redistribution, detailed carcass compliance, thermal/wear evolution, reverse rolling, and contact re-entry unless separately added and verified.

The principal model sources are [Deur2002], [Tsiotras2004], and [Chen2022]. Literature parameter sets used for reproduction remain labeled **[published_reference]**. Geometry or profile choices introduced only for project experiments are **[assumed_design]**. Missing robot-specific tire/contact quantities remain **[open_item]**.

This section defines a **numerical reference tire model**. It does not establish that:

- the selected load shape is the measured pressure distribution of a specific robot tire;
- the LuGre parameter set is experimentally identified for that tire;
- numerical agreement with another solver is physical validation;
- the tire model is valid through wheel lock, reverse rolling, or contact loss.

Those claims require the verification and validation evidence in Sec. V-A and V-F.
