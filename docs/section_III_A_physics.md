# III-A. Pressure and Deformation Representation for the Physics Reference

This section defines the physical state supplied to the pressure-aware predictor and the causal reference transition used to generate training/evaluation targets. It is deliberately separated from the network architecture in III-B: III-A specifies **what physical information exists and how the reference state evolves**, while III-B specifies how Member B encodes and learns from that information.

**Canonical interface.** The reference field, pressure/load representation, feature order, source versions, and closure state must match [`parameter_manifest.md`](parameter_manifest.md) and the dataset schema used by V-E. A predictor configuration may use a full sampled field or an explicitly declared encoding, but it may not mix representations silently between training and evaluation.

**Claim boundary.** The exact distributed bristle field is available in the numerical reference solver. It is not assumed to be directly measurable on a real robot. Any deployment claim requires a separately defined estimator, reconstruction, or learned state representation.

## III-A.1. Pressure / Normal-Load Representation

The reference contact model uses the normal line load

$$
q(\zeta)\quad[\mathrm{N/m}],\qquad \zeta\in[0,L_c],
$$

with

$$
q(\zeta)\ge0,
\qquad
\int_0^{L_c}q(\zeta)\,d\zeta=F_z.
$$

The predictor-side pressure/load information is represented in one of two declared forms:

1. a source-backed shape-parameter vector $\boldsymbol\theta_q$; or
2. ordered samples of $q(\zeta)$ on the declared spatial grid.

For sampled input,

$$
\mathbf q_k
=
\begin{bmatrix}
q(\zeta_1,t_k) &
q(\zeta_2,t_k) &
\cdots &
q(\zeta_N,t_k)
\end{bmatrix}^{T}.
$$

A discrete normalization check uses the same declared quadrature weights as the force integral:

$$
\sum_{j=1}^{N}w_j\,q(\zeta_j,t_k)\approx F_z.
$$

**Why the representation is declared explicitly.** Pressure-aware prediction is only meaningful if the model receives reproducible spatial-load information. A parameter vector and a sampled profile are different input spaces; changing between them without versioning would make training and evaluation incomparable.

**Current profile scope.** Uniform and source-backed nonuniform profiles from II-B are supported. A new project-specific pressure law is not introduced without data or a mechanical identification argument. If a profile coefficient is not source-backed or frozen in the manifest, it remains **[open_item]**.

## III-A.2. Distributed Deformation-Memory State

The physical reference state is

$$
\mathbf z(\zeta,t)
=
\begin{bmatrix}
z_x(\zeta,t)\\
z_y(\zeta,t)
\end{bmatrix}.
$$

At control/prediction sample $t_k$,

$$
\mathbf z_k(\zeta)=\mathbf z(\zeta,t_k).
$$

For an explicit $N$-node representation,

$$
\mathbf z_{k,\mathrm{grid}}
=
\begin{bmatrix}
z_x(\zeta_1,t_k),\ldots,z_x(\zeta_N,t_k),
z_y(\zeta_1,t_k),\ldots,z_y(\zeta_N,t_k)
\end{bmatrix}^{T}.
$$

**Why distributed memory is retained.** Instantaneous slip does not uniquely determine the transient force when the bristle field carries prior deformation history. The full field is therefore the numerical reference state used to generate physically consistent trajectories.

**Oracle-state versus operational-state experiments.** Supplying the exact solver field to a predictor is an **oracle-memory diagnostic**. It is useful for asking whether memory information has value, but it does not prove that the same state is available from onboard sensing. An operational predictor must instead use an estimator or encoding generated only from permitted present/past information.

## III-A.3. Physical Admissibility and Information Boundary

The representation is accepted only inside the declared baseline tire-model domain:

- $F_z>0$;
- $q(\zeta)\ge0$;
- $\int_0^{L_c}q(\zeta)\,d\zeta=F_z$;
- forward-rolling contact with the declared inflow edge;
- inherited/warm-started memory rather than per-sample reset;
- no undocumented clipping of $\mathbf z$ or force outputs;
- no realized future plant state supplied as a current predictor input.

Reverse rolling, contact loss/re-entry, and continuation through wheel lock remain outside the baseline domain until a verified extension is supplied.

**Why information availability is part of the physics contract.** The research question is candidate-conditioned prediction. If future wheel speed, future force, or future teacher state is supplied to the predictor, the reported accuracy no longer corresponds to an implementable causal prediction problem.

## III-A.4. Reference State Equation

The reference transition follows the distributed LuGre PDE from II-B,

$$
\frac{\partial z_i}{\partial t}
+
a(t)\frac{\partial z_i}{\partial\zeta}
=
v_{ri}(t)-C_i(t)z_i,
\qquad i\in\{x,y\},
$$

with

$$
a(t)=|\omega(t)r_w|.
$$

For forward rolling,

$$
\mathbf z(0,t)=\mathbf0.
$$

At $a=0$, the transport term vanishes and the local dynamics reduce to the reaction ODE without division by transport speed.

The normal line load $q(\zeta)$ is not a direct coefficient of this selected PDE. Under prescribed kinematics, changing only $q$ therefore changes force weighting but not the state trajectory directly. Under coupled wheel dynamics, force changes alter later $\omega$ and slip, so a pressure-shape change can affect later memory indirectly.

## III-A.5. Characteristic-Based Reference Transition

Under a frozen-input numerical substep $\Delta t$, the characteristic satisfies

$$
\frac{d\zeta}{dt}=a.
$$

Along that characteristic,

$$
\dot z_i+C_i z_i=v_{ri}.
$$

For a target point whose characteristic foot remains inside the patch,

$$
\zeta_f=\zeta-a\Delta t,
$$

and the frozen-coefficient update is

$$
z_i^{k+1}(\zeta)
=
z_i^k(\zeta_f)e^{-C_i\Delta t}
+
\frac{v_{ri}}{C_i}
\left(1-e^{-C_i\Delta t}\right).
$$

The previous value at $\zeta_f$ is obtained from the declared spatial interpolation rule.

**Why residence time replaces the full step at an inflow crossing.** A tread element that enters the patch during the current step has not been in contact for the full $\Delta t$. For constant positive $a$, its residence time is

$$
\tau=\frac{\zeta}{a},
$$

so the inflow update is

$$
z_i^{k+1}(\zeta)
=
\frac{v_{ri}}{C_i}
\left(1-e^{-C_i\tau}\right).
$$

When $C_i\to0$,

$$
\frac{1-e^{-C_i\tau}}{C_i}\rightarrow\tau.
$$

A stable implementation may evaluate the small-argument ratio through

$$
\frac{1-e^{-u}}{u}
=
-\frac{\operatorname{expm1}(-u)}{u}.
$$

**Implementation-status note.** Interpolation rule, quadrature rule, coefficient sampling within a substep, and small-$C_i$ tolerance are project numerical choices, not new tire physics. Their frozen values belong in the reference-solver configuration and V-A verification artifacts.

## III-A.6. Force/State Output of the Physics Reference

After the field is advanced, II-B computes

$$
F_x^w
=
\int_0^{L_c}\mu_x(\zeta,t)\,q(\zeta)\,d\zeta,
$$

$$
F_y^w
=
\int_0^{L_c}\mu_y(\zeta,t)\,q(\zeta)\,d\zeta,
$$

and

$$
M_z
=
\int_0^{L_c}
\left(\frac{L_c}{2}-\zeta\right)
\mu_y(\zeta,t)\,q(\zeta)\,d\zeta.
$$

The reference transition therefore returns both observable tire outputs and the next internal state required for causal rollout.

A paper-facing reference sample contains, at minimum, the current wheel-local kinematics, $F_z$, declared pressure/load representation, current memory representation, tire-model version/parameters, candidate actuator input/state when applicable, and the aligned targets $(F_x^w,F_y^w,M_z)$ plus next-state metadata.

## III-A.7. Candidate-Conditioned Causal Transition

For candidate braking, each candidate starts from the same current wheel/tire state and is propagated independently. With drive torque omitted in the braking scenarios, the wheel equation is

$$
J_w\dot\omega
=
-T_b^{applied}
-r_wF_x^w.
$$

The causal chain is

$$
T_b^{applied}
\longrightarrow
\omega
\longrightarrow
\mathbf v_r
\longrightarrow
\mathbf z
\longrightarrow
(F_x^w,F_y^w,M_z).
$$

**Why candidate states are deep-copied.** Candidate $j+1$ must not inherit the hypothetical state reached while evaluating candidate $j$. Otherwise candidate ordering would change the predicted results and violate the finite-set controller contract in Sec. IV.

Only the selected/applied command advances the operating plant state.

## III-A.8. Prescribed-Motion and Coupled-Candidate Modes

Two distinct reference-generation modes are retained.

### (a) Prescribed-motion trajectories

The external wheel-local motion history is supplied. These trajectories isolate tire-model and numerical behavior because the tire force does not feed back into the prescribed kinematics.

### (b) Causal braking-candidate trajectories

Current wheel-center kinematics, current $F_z$, pressure representation, tire parameters, actuator state, and candidate request are supplied at the start of the local horizon. Wheel speed and tire memory evolve through the coupled transition.

**Why the modes are not mixed.** A model trained on prescribed future kinematics must not be described as if it has solved the fully coupled candidate problem. The dataset/schema must label the generation mode so Member B and V-E can separate the two use cases.

## III-A.9. Reduced-Order LuGre Baseline Interface

The project includes a calibrated reduced-order dynamic LuGre baseline for the accuracy–cost comparison in V-C/V-E. It is a comparator, not an exact aggregate identity unless a derivation establishing that identity is supplied.

If the project retains the empirical closure

$$
\dot{\bar z}_i
=
v_{ri}
-
C_i\bar z_i
-
\kappa\frac{a}{L_c}\bar z_i,
\qquad i\in\{x,y\},
$$

then the additional $\kappa$ term is labeled **[assumed_design / calibrated]** unless an external derivation is cited. $\kappa$ is calibrated only on designated training trajectories; held-out trajectories remain untouched.

**Why the ROM is kept strong.** The paper asks whether retaining distributed pressure/memory information provides measurable value. Weakening the baseline would invalidate that comparison. If a calibrated ROM matches the distributed reference sufficiently well over part of the domain, that is a reportable boundary of the proposed method.

## III-A.10. Claim Boundary and Handoff to III-B

III-A defines the physical reference state and transition; it does not claim that:

- the full bristle field is directly measurable;
- the selected load shape is experimentally identified for the robot;
- the numerical reference is a physical ground truth;
- a learned model preserves the reference state outside its tested domain.

III-B must state exactly which subset or encoding of $(\mathbf q_k,\mathbf z_k)$ is supplied to the network, how it is normalized/resampled, and how any recurrent or latent state is updated. Those architecture choices must remain consistent with the causal information boundary defined here.
