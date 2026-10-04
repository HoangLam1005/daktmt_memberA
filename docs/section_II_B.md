## II-B. Distributed contact mechanics and tire memory

The tire contact patch is represented by a longitudinal spatial coordinate $x \in [0, L]$ with two internal bristle deflection states $\mathbf{z}(x, t) = [z_x(x, t), z_y(x, t)]^T$. The coordinate increases monotonically from the leading edge ($x = 0$) to the trailing edge ($x = L$). Contact forces are expressed in the wheel-fixed frame ($C$), with forward ($x$), leftward ($y$), and upward ($z$) positive axes (ISO standard), denoting the reaction force exerted by the road onto the wheel. The road-relative sliding velocity of the rubber elements is:
$$\mathbf{v}_r = [V_x - r\omega, V_y]^T = [v_{rx}, v_{ry}]^T$$

Our implementation strictly adheres to Eqs. (A1)–(A8) defined in [model_spec.md](model_spec.md). The hyperbolic transport–reaction equation preserves the local deformation history across the contact area, while the sliding speed $s = \|\mathbf{v}_r\|_2 = \sqrt{v_{rx}^2 + v_{ry}^2}$ isotropicly couples the longitudinal and lateral relaxation coefficients $C_i(t)$. During forward rolling ($a(t) = |\omega r| > 0$), the inflow boundary condition at the leading edge is zero:
$$\mathbf{z}(0, t) = \mathbf{0}$$
At zero transport speed ($a = 0$), the partial differential equation degenerates into a set of independent local ordinary differential equations (ODEs), and no inflow boundary condition is imposed. The initial bristle deformation profile $\mathbf{z}(x, 0)$ constitutes an essential state vector of the dynamic system rather than an algebraic variable reset at each discrete prediction step.

The non-negative normal line load $p(x) \ge 0$, expressed in $\text{N/m}$, integrates along the contact patch to the total vertical wheel load $F_z$:
$$\int_0^L p(x)\, dx = F_z$$
Three distribution families are supported at identical total load: uniform, asymmetric trapezoidal, and symmetric quartic profiles. Under purely prescribed kinematics, the normal load distribution does not alter the internal bristle deflection field $\mathbf{z}(x, t)$ because the transport–reaction equation is load-independent. Instead, $p(x)$ modulates the macroscopic forces through the traction stress integral:
$$\mathbf{F} = \begin{bmatrix} F_x \\ F_y \end{bmatrix} = \int_0^L \boldsymbol{\sigma}(x, t)\, p(x)\, dx$$
When wheel spin is dynamically coupled to road traction via the wheel rotational equation $I_w \dot{\omega} = -T_b - r F_x$, the normal load weighting indirectly alters future wheel slip. The self-aligning moment $M_z$ is integrated using the physical geometric moment arm $(L/2 - x)$ about the contact patch center:
$$M_z = \int_0^L \left(\frac{L}{2} - x\right) \sigma_y(x, t)\, p(x)\, dx$$

The constitutive formulation follows the distributed LuGre tire model with an explicit load-normalized parameter convention. In this study, camber angle, lateral contact width variations, carcass structural compliance, and thermal/wear transients are omitted. These simplifications define the numerical scope of this investigation; the nominal parameters serve as a canonical physical reference rather than an experimentally identified tire of a specific delivery robot. Refer to the foundational papers for [source equations](https://dcsl.gatech.edu/papers/vsd04R.pdf) (Velenis et al., 2005) and [parameter values](https://skoge.folk.ntnu.no/prost/proceedings/ifac2002/data/content/00284/284.pdf) (Deur, 2001). The comprehensive unit and sign conventions are documented in [model_spec.md](model_spec.md).

Illustrative figure: [figures/contact_patch.png](figures/contact_patch.png). In the complete manuscript, equation references map to Eqs. (A1)–(A8) without altering their mathematical definitions.
