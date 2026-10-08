# V-A. Reference-Model Verification and Reproducibility Evidence

This section reports the numerical evidence used to decide whether Member A's distributed LuGre implementation can be used as a **model-relative numerical reference**. The claim level is verification of the selected equations and implementation, not physical validation of a robot tire. Agreement with another numerical solver, convergence under refinement, or successful special-case tests do not establish real-world tire accuracy.

**Evidence source.** Numerical values in this section are valid only when traceable to `reference_verification_report.md`, automated-test logs, refinement CSV files, independent-solver comparison logs, and pilot-trajectory coarse/fine records. If an artifact is missing, the corresponding result must be marked **[open_item]** or removed rather than reconstructed from memory.

**Data-quality boundary.** A trajectory may be labeled `verified_reference` only after the verification gates relevant to that generation mode pass. `synthetic_debug` data remain excluded from paper-facing accuracy claims.

## V-A.1. Verification Architecture

**Why multiple verification layers are required.**

No single numerical check is sufficient. The protocol uses four complementary layers:

1. limiting/known-case and consistency tests;
2. spatial and temporal refinement;
3. comparison with an independently implemented solver;
4. trajectory-level coarse/fine gates on the actual pilot generation modes.

A literature-conditioned reproduction is treated separately because reproducing one published configuration tests source interpretation but is still not a measurement-based validation of the representative robot.

The Member A requirements are mapped as follows:

| Test ID | Verification target | Current evidence status |
|---|---|---|
| `A-T1` | Units and force/sign convention | Automated sign checks reported; complete unit-equivalence trace remains in the verification report |
| `A-T2` | Load normalization / non-negative distribution | Automated normalization checks reported; per-profile quadrature/non-negativity evidence must remain archived |
| `A-T3` | Limiting / known-solution behavior | Covered by special-case tests including inflow and zero-transport behavior |
| `A-T4` | Spatial and temporal refinement | Completed summary results reported below; full levels/norms remain an evidence artifact |
| `A-T5` | Independent numerical solver | Independent upwind method-of-lines + BDF comparison reported |
| `A-T6` | Memory behavior | Automated memory tests and matched memory ablations reported |
| `A-T7` | Longitudinal/lateral coupled specialization | **[open_item / partial]** unless explicit coupled-slip tests are identifiable in the detailed log |
| `A-T8` | Literature-conditioned reproduction | **[partial]**; reconstructed case exists, but digitized published-curve comparison remains unavailable |

## V-A.2. Automated Limiting-Case and Consistency Tests

The current reference implementation reports **14 automated tests** covering the implemented limiting and consistency cases, including:

- limiting-case behavior;
- inflow residence handling;
- normal-load normalization;
- force/sign conventions;
- distributed-state memory;
- Eulerian damping evaluation;
- candidate-state isolation.

**Why candidate-state isolation is tested.** Sec. IV evaluates multiple hypothetical brake requests from one physical current state. Each candidate must therefore start from an independent copy of the same $(\omega,\mathbf z)$ state. A failure of this test would make the result depend on candidate evaluation order rather than candidate physics.

**Interpretation.** Passing the automated suite shows that the tested implementation behaviors are internally consistent with the declared model contract. It does not show that every model regime is covered. In particular, `A-T7` must remain partial until its combined-slip specialization/symmetry checks are explicitly identified in the evidence package.

## V-A.3. Spatial Refinement

**Why spatial refinement is evaluated separately.**

The Method-of-Characteristics solver still contains interpolation/remapping and force-quadrature error even though the frozen reaction subproblem has an analytical exponential update. Spatial convergence must therefore be checked independently of time-step convergence.

Across the archived spatial-refinement configurations, the tested field error decreased by a factor of **38.88** from the coarse to the refined configuration.

This is an empirical refinement result, not a rigorous global bound.

The evidence record must retain, for every spatial level:

- grid definition / node count;
- interpolation rule;
- force quadrature rule;
- tested field or output quantity;
- error norm;
- numerical result;
- acceptance rule.

**No inferred convergence order without data.** The manuscript must not report an observed spatial order unless it is computed from the archived multi-level errors rather than inferred from the reduction factor alone.

## V-A.4. Zero-Transport Temporal Refinement

The zero-transport case isolates the local reaction integration from advective remapping. In the archived temporal study, reducing

$$
\Delta t=4\ \mathrm{ms}
$$

to

$$
\Delta t=0.5\ \mathrm{ms}
$$

reduced the tested error by a factor of **63.95**.

**Why the zero-transport case is useful.** When $a=0$, spatial transport vanishes. The test therefore probes the temporal/reaction implementation without mixing in interpolation error from characteristic remapping.

As with the spatial study, the full evidence must retain every tested time-step level, the reference quantity, norm, and acceptance threshold. The factor **63.95** is an observed result for the stored study, not a guaranteed error reduction for arbitrary trajectories.

## V-A.5. Independent-Solver Cross-Check

The primary characteristics-based reference implementation is compared with an independently implemented **upwind method-of-lines solver integrated with BDF**.

On the finest archived comparison grid, the reported maximum force discrepancy is **0.062% of wheel load**.

**Why an independently structured solver is used.** Re-implementing the same characteristic interpolation/update sequence would risk reproducing the same software mistake twice. An Eulerian upwind/MOL formulation provides a structurally different numerical path while solving the same selected PDE.

**Claim boundary.** Two implementations can agree and still share an incorrect model equation, sign convention, or source interpretation. The independent-solver result therefore complements — but does not replace — limiting-case, sign/unit, refinement, and literature-reproduction checks.

The archived comparison must identify the exact discrepancy definition, force component or vector norm, normalization by $F_z$, comparison horizon, grid, and test case. Without that definition, the percentage alone is not reproducible.

## V-A.6. Pilot-Trajectory Coarse/Fine Gates

Every pilot trajectory intended for downstream reference use is checked against a coarser/finer numerical configuration before receiving a verified label.

The largest currently reported force discrepancies are:

- **0.021% of wheel load** for prescribed-motion trajectories;
- **0.134% of wheel load** for causal braking-candidate trajectories.

**Why the two trajectory classes are reported separately.**

Prescribed-motion trajectories receive an externally supplied kinematic history. Candidate-braking trajectories instead propagate wheel speed and tire memory causally under the candidate brake request. The latter therefore includes the feedback path

$$
T_b^{applied}
\rightarrow
\omega
\rightarrow
\mathbf v_r
\rightarrow
\mathbf z
\rightarrow
F_x^w.
$$

A single pooled discrepancy would hide the different numerical problems.

These percentages are observed coarse/fine discrepancies on the archived pilot set; they are not worst-case guarantees over the admissible domain.

## V-A.7. Pressure-Shape and Memory Isolation Checks

Pressure and memory ablations change one factor at a time.

For pressure-shape comparisons,

$$
\int_0^{L_c}q_1(\zeta)\,d\zeta
=
\int_0^{L_c}q_2(\zeta)\,d\zeta
=
F_z.
$$

Thus the comparison isolates spatial load shape rather than total vertical load.

For memory comparisons, the instantaneous external inputs are matched while the declared memory representation is changed or removed according to the ablation.

**Why these are matched tests.** If pressure shape, total load, kinematics, and memory history all change simultaneously, any force difference cannot be attributed to the factor under study. The same matched-comparison principle is used later in V-C/V-E.

**Interpretation boundary.** A successful numerical ablation does not identify the true pressure profile of a robot tire and does not prove that the distributed bristle field is physically observable.

## V-A.8. Literature-Conditioned Reproduction

A source-conditioned cornering response has been reconstructed as a reproduction check.

`A-T8` remains **[partial]** because the current evidence package does not include both:

1. a digitized comparison against the corresponding published curve; and
2. an independent measurement-based validation dataset.

Before `A-T8` is marked complete, the archive must identify:

- exact paper / figure / table;
- source parameter set;
- excitation conditions;
- any digitization procedure and uncertainty;
- comparison metric;
- observed discrepancy.

**Why reproduction is not validation.** Matching a published simulation or model curve primarily tests interpretation of the source formulation and parameters. It does not demonstrate that the selected model reproduces the forces of the representative robot tire.

## V-A.9. Reproducibility Record and Reference Label

The paper-facing verification summary must be reconstructible from versioned artifacts:

- `reference_verification_report.md`;
- automated-test log;
- spatial-refinement CSV;
- temporal-refinement CSV;
- independent-solver comparison log;
- pilot coarse/fine comparison log;
- literature-reproduction files;
- model / parameter / sign-convention version identifiers.

A reference trajectory record must also preserve the generation mode, spatial grid, solver step, current-state initialization or warm-up artifact, load-shape ID, tire parameter version, and any candidate actuator state required to reproduce the run.

**Reference-label rule.**

- `synthetic_debug`: generated before the required numerical gates close;
- `verified_reference`: generated within the declared domain after the relevant numerical gates close;
- physical-validation terminology is reserved for future comparison against appropriate independent measurements.

## V-A.10. Verification Claim Boundary

The current evidence supports the claim that the selected distributed LuGre implementation has undergone numerical verification for the tested configurations.

It does **not** establish:

- a rigorous global error bound;
- physical validation of a specific robot tire;
- correctness outside the tested operating domain;
- validity through wheel lock, reverse rolling, or contact loss;
- a closed-loop safety guarantee for the controller.

Those stronger claims require the separate model-validation, robustness, and closed-loop evidence described in V-E/V-F.
