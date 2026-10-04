# Đặc tả mô hình Member A — phiên bản 1.0

Phạm vi: mô hình lốp số phục vụ PINN/SIL; chưa phải lốp robot đã nhận dạng. Nguồn tham số thực thi duy nhất là `parameter_registry.csv`. Bản Excel là bản duyệt, không được đọc bởi solver.

## A01–A02: lựa chọn và phạm vi

Chọn Distributed LuGre một chiều không gian, hai trạng thái $(z_x(x,t), z_y(x,t))$ [$\text{m}$]. Miền tọa độ $x \in [0, L]$ đi từ mép trước vào tiếp xúc (inflow) đến mép sau (outflow). Tọa độ thân tương ứng $X = L/2 - x$. Hệ trục bánh xe: $x$ hướng trước, $y$ sang trái, $z$ hướng lên; lực xuất ra là lực tiếp xúc tác dụng **lên bánh xe/thân xe**. Hai trục dùng chung chuẩn vận tốc trượt nên có hiện tượng ghép trượt kết hợp (combined slip); không thêm phép chiếu lực nhân tạo vào vòng tròn ma sát.

Mô hình giữ lại: hiệu ứng vận chuyển cao su, lịch sử biến dạng sợi bristle, đường cong ma sát Stribeck phi tuyến, áp suất tiếp xúc không đều và mô-men tự định hướng $M_z$ do lực ngang phân bố. Mô hình bỏ qua: góc đặt bánh camber, sự thay đổi vận tốc trượt dọc theo $x$, độ đàn hồi thân lốp (carcass compliance), nhiệt độ, nước/ẩm, biến dạng đàn hồi thân bánh xe, bản đồ áp suất 2D theo bề rộng và sự phụ thuộc của hệ số ma sát vào tải trọng. Áp suất ở đây là **mật độ tải đường pháp tuyến $p(x)$ theo đơn vị $\text{N/m}$**, không phải áp suất diện tích $\text{Pa}$. Không tự suy diễn bề rộng khi chưa có dữ liệu đo đạc thực tế.

Mô hình LuGre tập trung (Point LuGre) chỉ lưu giá trị trung bình trạng thái nhưng cần giả thiết đóng (closure) cho phần vật liệu thoát khỏi vệt tiếp xúc; trong khi đó, solver phân bố này lưu giữ trực tiếp toàn bộ trường biến dạng $z(x,t)$. Mô hình rút gọn (ROM) trong gói bàn giao là mô hình đối chứng hai trạng thái được hiệu chỉnh riêng trên tập dữ liệu huấn luyện. Gói này không khẳng định LuGre vượt trội hơn mọi mô hình Fiala hoặc Pacejka chuyển tiếp; mô hình được lựa chọn vì phù hợp trực tiếp với câu hỏi nghiên cứu về lịch sử biến dạng và trọng số phân bố tải trọng.

## A03: phương trình A1–A9

**(A1) Kinematics và quy ước dấu.**

Vận tốc cao su tương đối so với mặt đường theo hệ tọa độ bánh xe:

$$
\mathbf{v}_r = (V_x - r\omega, \, V_y), \qquad s = \|\mathbf{v}_r\|_2 = \sqrt{(V_x - r\omega)^2 + V_y^2}, \qquad a = |r\omega|
$$

- Ở chế độ phanh tiến: $r\omega < V_x \implies v_{rx} > 0$, lực ma sát ở trạng thái ổn định $F_x < 0$.
- Ở chế độ kéo tiến: $r\omega > V_x \implies v_{rx} < 0$, lực ma sát ở trạng thái ổn định $F_x > 0$.
- Chuyển động ngang: $V_y > 0 \implies F_y < 0$ ở trạng thái ổn định.
- Khi nhả slip ($v_r = 0$), lực tiếp xúc vẫn có thể tồn tại do năng lượng biến dạng tích lũy của các sợi bristle; không bắt buộc $\mathbf{F} \cdot \mathbf{v}_r < 0$ tại mọi thời điểm chuyển tiếp.

Mô hình chỉ hỗ trợ chiều chuyển động tiến ($\omega \ge 0$). Dấu giá trị tuyệt đối trong $a = |r\omega|$ không đồng nghĩa với việc hỗ trợ lùi xe: khi đổi chiều chuyển động cần phải đổi mép vào và ánh xạ lại toàn bộ trường biến dạng. Giao diện bánh xe từ chối biến cố dừng hẳn hoặc quay ngược. Hệ số trượt dùng để báo cáo:

$$
\kappa = \frac{r\omega - V_x}{\max(|V_x|, \, \epsilon_v)}, \qquad \alpha = \operatorname{atan2}(V_y, \, V_x)
$$

Lưu ý: Phương trình đạo hàm riêng (PDE) sử dụng trực tiếp các thành phần vận tốc, tuyệt đối không chia cho hệ số trượt $\kappa$.

**(A2) Đường cong ma sát Stribeck.**

$$
g(s) = \mu_k + (\mu_s - \mu_k) e^{-(s / v_s)^\gamma}
$$

Trong đó: $g(s)$ là đại lượng không thứ nguyên, $\mu_s \ge \mu_k > 0$, $v_s > 0$, $\gamma > 0$. Không nhầm lẫn với các biến thể $g$ có thứ nguyên lực ($\text{N}$) hoặc chiều dài ($\text{m}$).

**(A3) Hệ số suy giảm.**

$$
C_i(s) = \frac{\sigma_{0i} s}{g(s)} \quad [\mathrm{s}^{-1}], \qquad i \in \{x, y\}
$$

Không dùng $|v_{ri}|$ riêng lẻ cho từng trục. Tại $s = 0$, ta có $C_i = 0$, mô hình chuyển tiếp liên tục mà không cần thêm giá trị $\epsilon$ nhân tạo vào biểu thức vật lý.

**(A4) PDE và đạo hàm vật chất.**

$$
\partial_t z_i + a \partial_x z_i = v_{ri} - C_i z_i, \qquad D_t z_i = \partial_t z_i + a \partial_x z_i
$$

Số hạng nguồn $v_{ri}$ và hệ số suy giảm $C_i$ không phụ thuộc vào áp suất $p$ khi vận tốc đã được áp đặt trước. Việc thay đổi dạng phân bố áp suất mà giữ nguyên động học sẽ không làm thay đổi trường biến dạng $z(x,t)$; tuy nhiên khi ghép nối với phương trình quay của bánh xe, sự thay đổi của lực sẽ làm thay đổi $\omega$ và gián tiếp thay đổi $z$.

**(A5) Điều kiện đầu và điều kiện biên.**

$$
z_i(x, 0) = z_{i0}(x); \qquad z_i(0, t) = 0 \quad \text{khi } a > 0
$$

Không đặt điều kiện biên tại mép ra ($x = L$). Tại $a = 0$ (vệt bánh đứng yên), phương trình trở thành hệ ODE cục bộ độc lập tại mọi nút (kể cả tại $x = 0$); không áp đặt biên inflow cho vệt bánh đứng yên. Khi bánh xe bắt đầu quay lại, mép vào nhận vật liệu mới chưa biến dạng ($z = 0$), trong khi các nút bên trong tiếp tục giữ nguyên lịch sử biến dạng trước đó. Trạng thái đầu $z_0$ lấy từ trường ổn định, warm-up hoặc frame trước; tuyệt đối không reset về 0 ở mỗi frame.

**(A6) Hệ số ma sát cục bộ và tải tiếp tuyến.**

$$
\mu_i(x, t) = -[\sigma_{0i} z_i + \sigma_{1i} \partial_t z_i + \sigma_2 v_{ri}], \qquad q_i(x, t) = p(x, t) \mu_i(x, t)
$$

Thứ nguyên: $\sigma_{0i}$ có đơn vị $\mathrm{m}^{-1}$; $\sigma_{1i}, \sigma_2$ có đơn vị $\mathrm{s/m}$; $q_i$ là mật độ lực tiếp tuyến có đơn vị $\mathrm{N/m}$. Thành phần giảm chấn sử dụng đạo hàm **Eulerian** $\partial_t z_i$, được tính từ PDE thông qua gradient không gian bậc hai:

$$
\partial_t z_i = v_{ri} - C_i z_i - a \partial_x z_i
$$

Biên inflow cố định thỏa mãn $\partial_t z_i(0, t) = 0$ khi $a > 0$. Không thay thế bằng đạo hàm vật chất $D_t z_i$. Bộ tham số cơ sở có hệ số giảm chấn bằng 0 ($\sigma_1 = \sigma_2 = 0$); chỉ các bài test kiểm chứng chuyên biệt mới kích hoạt giảm chấn. Không xuất ứng suất diện tích $\text{Pa}$ khi chưa biết bề rộng vệt bánh xe.

**(A7) Phân bố tải trọng pháp tuyến.**

Đặt tọa độ không thứ nguyên $u = x/L \in [0, 1]$, mật độ tải pháp tuyến được biểu diễn:

$$
p(x) = \frac{F_z}{L} h(u), \qquad \int_0^1 h(u) \, du = 1
$$

Ba họ hàm áp suất được hiện thực:
- **Uniform (Đều):** $h(u) = 1$.
- **Trapezoid (Hình thang bất đối xứng của Deur):**
  $$
  h(u) = \frac{2 b(u)}{1 + r_r - r_l}, \qquad b(u) = \begin{cases} 
  \frac{u}{r_l}, & u < r_l \\ 
  1, & r_l \le u \le r_r \\ 
  \frac{1 - u}{1 - r_r}, & u > r_r 
  \end{cases}
  $$
  với $0 < r_l < r_r < 1$ (giá trị chuẩn $r_l = 0.134, r_r = 0.707$).
- **Quartic (Bậc 4 đối xứng):** $h(u) = 30 u^2 (1 - u)^2$. Đây là đa thức $\mathrm{Beta}(3,3)$ được chuẩn hóa, dùng làm đối chứng hình học trơn.

Trên lưới rời rạc, tích phân sử dụng trọng số hình thang $w_j$ và chuẩn hóa tải trọng nút:

$$
p_j = \frac{F_z h_j}{\sum_k w_k h_k}
$$

Hệ thống lưu trữ cả sai số tích phân **trước khi chuẩn hóa** nhằm phát hiện trường hợp lưới quá thô. Tất cả $p(x) \ge 0$. Tải trọng đứng $F_z$ phải luôn dương ($F_z > 0$); biến cố mất tiếp xúc ($F_z \le 0$) cần một mô hình thoát/vào tiếp xúc riêng biệt.

**(A8) Lực tiếp xúc và mô-men tự định hướng.**

$$
F_i = \int_0^L q_i(x) \, dx \simeq \sum_j w_j q_{ij}, \qquad M_z = \int_0^L \left(\frac{L}{2} - x\right) q_y(x) \, dx
$$

Mô-men $M_z$ là yaw moment theo quy tắc bàn tay phải (trục $z$ hướng lên). Mô hình không tính đến mô-men do bề rộng vệt bánh xe, overturning moment hoặc mô-men cản lăn rolling resistance.

Phép quay lực sang hệ tọa độ thân xe:

$$
\mathbf{F}_b = R(\delta) \mathbf{F}_w, \qquad R(\delta) = \begin{bmatrix} \cos\delta & -\sin\delta \\ \sin\delta & \cos\delta \end{bmatrix}
$$

Mô-men tổng cộng tác dụng quanh trọng tâm xe bao gồm:

$$
M_{z,\text{total}} = x_w F_{by} - y_w F_{bx} + M_z
$$

Tuyệt đối không cộng $M_z$ hai lần trong mô hình xe.

**(A9) Thuật toán Method of Characteristics (MoC).**

Dọc theo đường đặc trưng $\frac{d\zeta}{dt} = a$, phương trình đạo hàm riêng trở thành phương trình vi phân thường:

$$
\frac{d z_i}{dt} + C_i z_i = v_{ri}
$$

Với đầu vào được giữ hằng trong bước tính $\Delta t$, xét chân đường đặc trưng $x_f = x - a \Delta t$:
- Nếu $x_f \ge 0$: Nội suy tuyến tính giá trị trạng thái cũ $z_{i,f} = z_i^n(x_f)$.
- Nếu $x_f < 0$: Đường đặc trưng xuất phát từ biên inflow, gán $z_{i,f} = 0$.

Thời gian phản ứng dọc theo đường đặc trưng là $h = \min(\Delta t, \, x/a)$ khi $a > 0$, và $h = \Delta t$ khi $a = 0$. Nghiệm cập nhật chính xác:

$$
z_i^{n+1} = z_{i,f} e^{-C_i h} + v_{ri} h \, \phi(C_i h), \qquad \phi(q) = -\frac{\operatorname{expm1}(-q)}{q} = \frac{1 - e^{-q}}{q}, \quad \phi(0) = 1
$$

Thừa số tích phân tương đương là $I = e^{\int C_i dt}$. Code sử dụng hàm `expm1` ở dạng suy giảm lũy thừa âm để triệt tiêu hiện tượng tràn số (overflow) và chia cho 0. Đầu vào biến thiên trơn được lấy tại điểm giữa (midpoint) của từng khoảng thời gian. Bắt buộc phải chia bước tại các thời điểm có bước nhảy gián đoạn. Sai số nội suy không gian vẫn tồn tại dù phương trình phản ứng được giải chính xác; không gọi đây là nghiệm PDE chính xác tuyệt đối.

## Ánh xạ nguồn và phép đổi đơn vị

- Tài liệu [Tsiotras, Velenis, Sorine (2004), §2, Eqs. (1)–(8)](https://dcsl.gatech.edu/papers/vsd04R.pdf) cung cấp cấu trúc PDE, hàm $g(s)$, lực tiếp xúc có giảm chấn Eulerian damping và chuẩn vận tốc trượt tổng hợp.
- Tài liệu [Deur (2002), §2 và Appendix B](https://skoge.folk.ntnu.no/prost/proceedings/ifac2002/data/content/00284/284.pdf) cung cấp bộ số lốp cơ sở và dạng phân bố hình thang.

Trong tài liệu của Deur: $g_D$ có đơn vị $\text{N}$, $\sigma_{0D}$ có đơn vị $\text{N/m}$, mật độ áp suất $p_D$ có giá trị trung bình bằng 1; phương trình lực có hệ số $1/L$ sau tích phân bề rộng. Quy đổi sang hệ chuẩn hóa ở đây bằng cách đặt:

$$
g = \frac{g_D}{F_{z0}}, \qquad \sigma_0 = \frac{\sigma_{0D}}{F_{z0}}
$$

Do bảng tham số của Deur cung cấp tích số $L \sigma_{0D}$ tại tải danh định $F_{z0} = 4000\text{ N}$ và $L = 0.303\text{ m}$:

$$
\sigma_{0x} = \frac{314000}{0.303 \times 4000} \approx 259.0759075907591 \; \mathrm{m}^{-1}
$$

$$
\sigma_{0y} = \frac{159200}{0.303 \times 4000} \approx 131.35313531353134 \; \mathrm{m}^{-1}
$$

Phép đổi đơn vị này giữ nguyên giá trị hệ số suy giảm $C_i$ và tổng lực ma sát tại tải trọng danh định. Khi khảo sát độ nhạy tải trọng, giá trị $\sigma_0$ chuẩn hóa này được giữ cố định (đây là giả thiết độ cứng tỷ lệ thuận với tải trọng của nghiên cứu, chưa phải kết quả nhận dạng độ nhạy tải thực tế). Bán kính bánh xe $r$, mô-men quán tính $I_w$ và thông số cơ cấu phanh là thiết kế benchmark, chưa đo trên robot thật.

## Giới hạn lực có thể kiểm tra đúng

Ở trạng thái ổn định (steady state) với $z_0$ hợp lệ và damping bằng 0:

$$
\|\mathbf{F}\|_2 \le g(s) F_z \le \mu_s F_z
$$

Với quá trình chuyển tiếp (transient) **đẳng hướng** ($\sigma_{0x} = \sigma_{0y} = \sigma_0$), miền trạng thái $\|\sigma_0 \mathbf{z}\|_2 \le \mu_s$ là tập bất biến. 

Với độ cứng **dị hướng** của bộ thông số cơ sở ($\sigma_{0x} \neq \sigma_{0y}$), không thể khẳng định vòng tròn đó bất biến cho mọi lịch sử kích thích đổi hướng. Khi đó, áp dụng chặn bảo thủ trên từng thành phần $|\sigma_{0i} z_i| \le \mu_s$ dẫn đến giới hạn lực tổng hợp:

$$
\|\mathbf{F}\|_2 \le \sqrt{2} \mu_s F_z
$$

Trạng thái ban đầu $z_0$ nằm ngoài miền giới hạn sẽ không thỏa mãn bất đẳng thức này. Do thành phần giảm chấn $\sigma_1$ và độ nhớt $\sigma_2$ đóng góp thêm lực trong quá trình chuyển tiếp, tuyệt đối không được áp đặt chặn Coulomb nhân tạo lên tổng lực để che giấu sai số giải thuật.

## Ghép quay bánh và miền áp dụng

Hàm `wheel_interface.reference_step` giải phương trình động lực học quay của một bánh xe:

$$
I_w \dot{\omega} = -T_b - r F_x
$$

(ở kịch bản benchmark phanh không có mô-men chủ động từ động cơ $T_{\text{drive}} = 0$). Mô hình cơ cấu chấp hành phanh:

$$
\dot{T}_b = \operatorname{clip}\left(\frac{T_{\text{cmd}} - T_b}{\tau_b}, \, -\dot{T}_{\max}, \, \dot{T}_{\max}\right), \qquad T_{\text{cmd}} \in [0, \, T_{\max}]
$$

Đây là giới hạn vật lý của cơ cấu chấp hành; không phải bộ cắt kẹp lực lốp. Tích phân sử dụng phương pháp điểm giữa (midpoint rule) với các bước con được chia nhỏ. Xung lực phanh được tính bằng tổng tích phân:

$$
\mathbf{I}_F = \sum_k \mathbf{F}_{\text{mid}, k} \Delta t_k
$$

tuyệt đối không dùng xấp xỉ $\mathbf{F}_{\text{end}} \cdot H$.

Các đại lượng $V_x, V_y, F_z$ và dạng phân bố áp suất được giữ hằng trong khoảng thời gian dự đoán (horizon); tốc độ góc $\omega$ và trường biến dạng $\mathbf{z}$ biến thiên liên tục. 

Biến cố $\omega \le 0$ bị từ chối rõ ràng bằng ngoại lệ, Member C cần bổ sung mô hình khóa bánh riêng trước khi mô phỏng dừng xe hoàn toàn. Bộ giải lốp thuần túy hỗ trợ trường hợp xe đứng yên ($a = 0$), nhưng giao diện quay bánh xe hiện tại chưa hỗ trợ chuyển trạng thái khóa bánh/đảo chiều. Gói Member A không bao gồm bộ ước lượng trạng thái (observer), mô hình xe 4 bánh đầy đủ, bộ điều khiển ZOCBF, mạng nơ-ron PINN hay firmware nhúng MCU.
