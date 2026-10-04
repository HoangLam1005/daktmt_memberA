# Báo cáo kiểm chứng reference solver Member A

Tất cả số liệu dưới đây được đọc trực tiếp từ file log của lần chạy hiện tại; không có số liệu giả lập kết quả PINN hoặc xe trong báo cáo này.

## 1. Mức bằng chứng và ngưỡng nghiệm thu (Verification Gates)

- **G0 (Formulation & Specification):** Đã xác định hệ phương trình vi phân đạo hàm riêng (PDE), thứ nguyên, quy ước dấu, điều kiện biên/đầu ($IC/BC$) và nguồn gốc tham số vật lý trong [model_spec.md](model_spec.md).
- **G1 (Algorithmic & Numerical Verification):** 14 kiểm thử đơn vị tự động thành công, cùng các thí nghiệm hội tụ không gian/thời gian và đối chiếu solver độc lập bên dưới. Solver kiểm tra độc lập sử dụng sai phân Upwind kết hợp bộ tích phân SciPy BDF (Method of Lines), hoàn toàn không gọi hàm MoC hay hàm tích phân phản ứng của solver chính. Đây là kiểm chứng thuật toán độc lập trong gói mã nguồn; chưa phải review chéo độc lập từ Thành viên D.
- **G2 (Phenomenological & Literature Consistency):** Tái dựng các điều kiện thử nghiệm của Deur et al. (Fig. 4), các tham số nguồn được quy đổi đơn vị tường minh. Do chưa có dữ liệu số hóa trực tiếp từ đồ thị gốc để tính toán sai số định lượng ($\mathrm{RMSE}$), bước này đóng vai trò xác nhận định tính đáp ứng chuyển tiếp.
- **G3 (Experimental Validation):** Hiện tại chưa có dữ liệu đo đạc thực nghiệm từ lốp thực của robot giao hàng.
- **G4 (Integrated Closed-Loop Verification):** Chưa thực hiện kiểm thử vòng kín với mô hình xe đầy đủ / PINN / ZOCBF của các thành viên B, C, D.

**Ngưỡng sai số định trước (Error Tolerances):**
Được khai báo trong registry trước khi chạy thử nghiệm:
- Chuẩn vô cùng sai khác lực tiếp xúc chuẩn hóa: $\frac{\Vert \Delta \mathbf{F} \Vert_{\max}}{F_z} < 0.02$ ($2\%$).
- Sai số RMS trường biến dạng bristle chuẩn hóa: $\frac{\mathrm{RMS}(\Delta z)}{\mu_s / \min(\sigma_{0x}, \sigma_{0y})} < 0.03$ ($3\%$).

Đây là mức chấp nhận cho bộ dữ liệu thí điểm (pilot dataset), không thay thế cho chặn sai số giải tích nghiêm ngặt (analytical error bounds). Việc so sánh lưới mịn / lưới thô là chỉ báo sai số thực nghiệm, không phải chặn sai số tuyệt đối.

## 2. Kiểm thử đơn vị và phân tích hội tụ số (Convergence Analysis)

File nhật ký: [`results/unit_tests.log`](results/unit_tests.log) ghi nhận **14/14 tests PASS**. Các kịch bản bao gồm:
- Zero input: $\mathbf{v}_r = \mathbf{0}, \mathbf{z} = \mathbf{0} \implies \mathbf{F} = \mathbf{0}$;
- Giới hạn $C_i \to 0$: thuần trượt / đàn hồi tuyến tính;
- Giới hạn dừng vận chuyển $a = 0$: bảo toàn điều kiện biên, giải nghiệm ODE địa phương;
- Thời gian lưu trú mép vào (inflow residence time $\tau = x/a$);
- Tính không âm và chuẩn hóa tích phân của áp suất: $p(x) \ge 0$, $\int_0^L p(x)\,dx = F_z$;
- Tính nhất quán về dấu và đối xứng lực: $F_x, F_y$ cùng chiều $v_{rx}, v_{ry}$;
- Chặn lực vật lý bảo thủ: $\Vert \mathbf{F} \Vert \le \mu_s F_z$ trong điều kiện trượt dừng isotropic;
- Bộ nhớ biến dạng bristle (tire dynamic memory);
- Eulerian damping tiêu tán năng lượng biến dạng;
- Mô-men tự chỉnh hướng $M_z$ và tải pháp tuyến $F_z$;
- Bất biến quay hệ trục tọa độ và cân bằng công suất ma sát $\dot{E} \ge 0$;
- Tính độc lập của trạng thái ứng viên (deep copy candidate state);
- Từ chối dữ liệu ngoài miền xác định (out-of-bounds rejection).

### 2.1. Hội tụ theo không gian (Spatial Refinement, $\Delta t = 0.0002\text{ s}$)

So với trường biến dạng dừng giải tích ($z_{\text{steady}}(x)$), sau hơn 2 chu kỳ hạt quét qua vệt tiếp xúc ($t > 2L/a$). Đây là kịch bản có vận chuyển ($a > 0$), đánh giá trực tiếp thuật toán quá độ (transient MoC solver):

| $N_x$ | $\Delta x\text{ [m]}$ | $\Delta t\text{ [s]}$ | $\mathrm{RMS}(\mathbf{z})\text{ [m]}$ | $\Vert \Delta \mathbf{F} \Vert / F_z$ |
| --- | --- | --- | --- | --- |
| 65 | 0.004734375 | 0.0002 | 2.111596454246543e-05 | 0.007178116270971008 |
| 129 | 0.0023671875 | 0.0002 | 8.48778651593251e-06 | 0.0028795533403942948 |
| 257 | 0.00118359375 | 0.0002 | 2.0870558519385882e-06 | 0.0007073721035547831 |
| 513 | 0.000591796875 | 0.0002 | 5.430864983995073e-07 | 0.00018391323092585517 |

Sai số RMS của trường biến dạng bristle giảm **38.881 lần** khi tăng mật độ lưới từ thô ($N_x = 65$) đến mịn ($N_x = 513$). Phương pháp nội suy tuyến tính bước chân đặc trưng tạo ra độ khuếch tán số học (numerical diffusion); không suy từ test này thành bậc hai theo không gian cho mọi số Courant. Khi $\Delta t$ nhỏ cố định với $\Delta x$ mịn, sai số tái nội suy (spatial remapping error) có thể chiếm ưu thế.

### 2.2. Hội tụ theo thời gian (Temporal Refinement, loại bỏ sai số vận chuyển với $a = 0$)

Đối chiếu với bộ giải chuẩn DOP853 (Runge-Kutta bậc 8) với dung sai khắt khe trên hệ phương trình vi phân biến thiên theo thời gian. Thí nghiệm này cô lập sai số đóng băng điểm giữa (midpoint freezing error); không đại diện cho toàn bộ sai số PDE khi $a > 0$:

| $\Delta t\text{ [s]}$ | $a\text{ [m/s]}$ | $\Vert \Delta \mathbf{z} \Vert_{\max}\text{ [m]}$ |
| --- | --- | --- |
| 0.004 | 0.0 | 3.1750837669665763e-07 |
| 0.002 | 0.0 | 7.942794250560227e-08 |
| 0.001 | 0.0 | 1.9860166592861915e-08 |
| 0.0005 | 0.0 | 4.9652404959253404e-09 |

Sai số giảm **63.946 lần** khi giảm bước thời gian từ $\Delta t = 0.004\text{ s}$ xuống $\Delta t = 0.0005\text{ s}$. Đối với đầu vào có bước nhảy gián đoạn, cần phân chia bước thời gian đúng tại thời điểm xảy ra biến cố.

### 2.3. Đối chiếu với Solver độc lập khi có vận chuyển ($a > 0$)

| $N_x$ | $\Delta t_{\mathrm{MoC}}\text{ [s]}$ | $\Vert \Delta \mathbf{F} \Vert_{\max} / F_z$ | $\mathrm{RMS}(\mathbf{z})\text{ [m]}$ |
| --- | --- | --- | --- |
| 65 | 0.00047318611987381704 | 0.004795662749383196 | 1.4173525147508959e-05 |
| 129 | 0.00023659305993690852 | 0.0024325719290850395 | 7.49322580194965e-06 |
| 257 | 0.00011829652996845426 | 0.001227159247557815 | 3.984591412225155e-06 |
| 513 | 5.9171597633136094e-05 | 0.0006172868050880967 | 2.1419139852276905e-06 |

Ở độ phân giải lưới mịn nhất ($N_x = 513$), sai khác lực cực đại chuẩn hóa đạt:
$$\frac{\Vert \Delta \mathbf{F} \Vert_{\max}}{F_z} = 0.000617287$$
Thí nghiệm này tinh chỉnh đồng thời $\Delta x$ và $\Delta t$ để giữ số Courant $\mathrm{Cr} \approx 0.4$. Khảo sát ban đầu giữ $\Delta t = 0.00025\text{ s}$ cho thấy sai khác giữa hai cách rời rạc dừng ở mức $0.26\% F_z$, do sai số thời gian / remapping không giảm cùng lưới; không dùng kết quả đó để tuyên bố hội tụ. Cả hai thuật toán đều có sai số không gian; sự đồng thuận là bằng chứng kiểm chứng tính toán (numerical verification), không phải kiểm chứng thực nghiệm lốp thật.

### 2.4. Ghép nối động lực học quay bánh và cơ cấu chấp hành (Wheel-Actuator Dynamics)

Phương trình vi phân quay bánh:
$$I_w \dot{\omega} = -T_b - r F_x$$
được giải đồng thời cùng biến dạng tiếp xúc lốp:

| $N_x$ | $\Delta t\text{ [s]}$ | $\Vert \Delta \mathbf{F} \Vert / F_z$ | $\Delta \omega\text{ [rad/s]}$ | $\Delta I\text{ [N}\cdot\text{s]}$ |
| --- | --- | --- | --- | --- |
| 129 | 0.002 | 0.0005274328689332898 | 0.019120785940149432 | 0.0856744698131119 |
| 257 | 0.001 | 5.186703121822353e-05 | 0.004746497480031309 | 0.021193293853558014 |
| 513 | 0.0005 | 8.302516351646092e-06 | 0.0011514832344197146 | 0.005375195702169748 |

Benchmark được đối chiếu với nghiệm siêu mịn ($N_x = 1025, \Delta t = 0.000125\text{ s}$). Cùng làm mịn không gian và thời gian ở phép thử ghép này. Solver chưa mô phỏng biến cố khóa cứng bánh xe; sự kiện $\omega \le 0$ sẽ phát sinh ngoại lệ rõ ràng.

## 3. Phân bố áp suất, chặn lực và độ nhạy tham số

- **Chuẩn hóa áp suất pháp tuyến:** Sai số cực đại của tổng tải sau chuẩn hóa trên tất cả các profile (uniform, trapezoidal, quartic): **4.441e-16 N**. Chi tiết xem [`results/pressure_normalization.csv`](results/pressure_normalization.csv) cho cả sai số trước chuẩn hóa và tọa độ centroid $x_c$. Tổng tải đúng bằng thuật toán chuẩn hóa không tự chứng minh hình dạng áp suất đủ mịn. Dạng uniform và quartic đối xứng được kiểm tra vị trí centroid chính xác tại $x_c = L/2$.
- **Giới hạn lực vật lý:** Solver không sử dụng hàm cắt ngọn nhân tạo (`clamp`) trên $z_i$, $C_i$ hoặc lực $\mathbf{F}$. Giới hạn lực được kiểm tra thỏa mãn chặn trượt dừng kết hợp và quá độ đẳng hướng (isotropic transient). Với quá độ dị hướng (anisotropic transient), áp dụng chặn từng thành phần bảo thủ như quy định trong [model_spec.md](model_spec.md), không mặc định giới hạn vòng tròn $\mu_s F_z$. Lực cản nhớt Eulerian damping không bị gộp vào chặn ma sát Coulomb giản lược.
- **Phân tích độ nhạy (Sensitivity):** File [`results/sensitivity.csv`](results/sensitivity.csv) ghi nhận kết quả khi thay đổi từng tham số $L, \sigma_{0x}, \sigma_{0y}, \mu_s, \mu_k, v_s, \gamma$ theo các tỷ lệ $0.8 / 1.0 / 1.2$, giữ nguyên tín hiệu kích thích và tải trọng $F_z$. Đây là khảo sát tham số số học, không phải khoảng tin cậy thực nghiệm.

## 4. Bằng chứng bộ nhớ động học và các nghiên cứu triệt tiêu (Ablations)

- **Bộ nhớ động học tiếp xúc (Dynamic Memory):** Hai kịch bản có cùng vận tốc trượt bằng 0 ($\mathbf{v}_r = \mathbf{0}$) và cùng tốc độ $a > 0$ có chênh lệch lực ban đầu là **3833.331 N** do lịch sử biến dạng $\mathbf{z}(x, 0)$ khác nhau. Khi vật liệu cũ thoát khỏi vệt tiếp xúc ($t \ge L/a$), chênh lệch này triệt tiêu hoàn toàn. Đồ thị [`figures/memory_ablation.png`](figures/memory_ablation.png) minh họa trực tiếp cơ chế này; không áp đặt bộ nhớ phải có lợi sau khi hệ thống đã quên trạng thái ban đầu.
- **Ảnh hưởng phân bố áp suất (Pressure Ablation):** File [`results/pressure_ablation.csv`](results/pressure_ablation.csv) và đồ thị [`figures/pressure_ablation.png`](figures/pressure_ablation.png) áp dụng cùng trường biến dạng $\mathbf{z}$ và cùng tải $F_z$, chỉ thay đổi phân bố $p(x)$; không so sánh các quỹ đạo khác nhau rồi quy sai khác cho áp suất.
- **Mô hình bậc giảm (Reduced-Order Model - ROM):** Hệ số đóng đối lưu $\kappa = 1.20916154$, được khớp trên 3 kịch bản huấn luyện riêng và đánh giá trên 2 kịch bản kiểm tra độc lập (held-out):

| Kịch bản (Case) | $\mathrm{RMSE}(\mathbf{F})\text{ [N]}$ | $\Vert \Delta \mathbf{F} \Vert_{\max} / F_z$ | $t_{\mathrm{wall, REF}}\text{ [s]}$ | $t_{\mathrm{wall, ROM}}\text{ [s]}$ |
| --- | --- | --- | --- | --- |
| 0 | 112.63775473715319 | 0.07710123953415575 | 0.14999860000170884 | 0.027009600000383216 |
| 1 | 98.64682398560929 | 0.04894541893370545 | 0.1628184000001056 | 0.026697299999796087 |

Thời gian thực thi (wall-clock runtime) là kết quả đo trên máy tính thử nghiệm, bao gồm overhead của Python trong phiên bản hiện tại. Kết quả chưa qua kiểm thử thống kê warm-up, không đại diện cho độ trễ trên vi điều khiển nhúng (MCU) và chưa đủ cơ sở để kết luận về khả năng tăng tốc khi triển khai thực tế.

## 5. Dữ liệu tham chiếu sinh ra (Delivered Reference Datasets)

Bao gồm **24 quỹ đạo động học** (kinematic trajectories) và **36 ví dụ ứng viên phanh** (braking candidates). Mỗi kịch bản đều được đối chiếu với nghiệm trên lưới mịn gấp đôi ($2 \times N_x, \frac{1}{2} \Delta t$). Sai số lực chuẩn hóa lớn nhất:
- Quỹ đạo động học: $\frac{\Vert \Delta \mathbf{F} \Vert_{\max}}{F_z} = 0.0002113$;
- Kịch bản ứng viên: $\frac{\Vert \Delta \mathbf{F} \Vert_{\max}}{F_z} = 0.00134189$.

Toàn bộ dữ liệu đều hữu hạn (finite, không có NaN/Inf), lưu trữ đầy đủ trường biến dạng $\mathbf{z}(x, t)$, không có biến cố clamp. Dữ liệu được chia tập theo kịch bản trước khi trích xuất cửa sổ thời gian; mô hình dự báo không được sử dụng thông tin tương lai chưa xuất hiện tại thời điểm ra quyết định.

## 6. Kịch bản dễ phát sinh sai số và giới hạn mô hình

1. **Đầu vào trượt gián đoạn:** Bước trượt thay đổi đột ngột không được phân đoạn thời gian có thể làm giảm bậc hội tụ; vệt tiếp xúc ngắn ở tốc độ cao với lưới thưa gây khuếch tán số học; thành phần cản damping lớn khiến gradient sai số ảnh hưởng trực tiếp đến lực tính toán.
2. **Quan hệ bước lưới - bước thời gian:** Giảm bước thời gian $\Delta t$ đơn thuần không thể bù đắp cho việc làm thô lưới không gian $\Delta x$. Solver MoC không bị ràng buộc điều kiện Courant (CFL) về tính ổn định của phản ứng, nhưng sai số vận chuyển (transport error) vẫn tồn tại.
3. **Các biến cố biên động học:** Hiện tượng đảo chiều quay, mất tiếp xúc mặt đường ($F_z \le 0$) và khóa cứng bánh xe ($\omega \le 0$) chưa được hỗ trợ trong giao diện hiện tại; cần mô hình vật lý thân xe và phép thử riêng biệt để xử lý.
4. **Giới hạn mô hình vật lý:** Mô hình chưa xét đến tính phi tuyến của tải trọng thực, góc nghiêng bánh xe (camber), độ mềm thân lốp (carcass compliance), hiệu ứng biến thiên nhiệt độ và bộ thông số thực nghiệm được nhận dạng trên robot thực.
5. **Phạm vi bộ dữ liệu:** Bộ dữ liệu thí điểm có quy mô tập trung và sử dụng một bộ tham số định danh duy nhất; không chứng minh khả năng tổng quát hóa ngoài miền dữ liệu hoặc bảo đảm an toàn điều khiển vòng kín (closed-loop safety).

Thành viên D cần thực hiện rà soát độc lập các ngưỡng kiểm chứng, file log và quy cách phân chia dữ liệu trước khi tiến hành các thử nghiệm chính thức. Không chuyển đổi nhãn dữ liệu thành dữ liệu đo đạc thực nghiệm (measured) hoặc đã được kiểm chứng thực tế (physically validated).
