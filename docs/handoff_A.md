# Bàn giao Member A

Bản triển khai: `A-moc-1.0.0`.

## Kết quả A01–A10

| Task | Tệp bàn giao | Trạng thái / Phạm vi |
|---|---|---|
| **A01** Phạm vi | [model_spec.md](model_spec.md) | Vệt tiếp xúc 1D, sợi cao su 2D, chiều tiến, IC/BC và bảng giả thiết. |
| **A02** Chọn LuGre | [source_audit.md](source_audit.md), [model_spec.md](model_spec.md) | Đã đối chiếu nguồn Deur/Tsiotras; chuẩn hóa độ cứng theo tải danh định. |
| **A03** Phương trình | [model_spec.md](model_spec.md) (A1–A9) | Khớp solver; giảm chấn Eulerian damping; tích phân lực và mô-men $M_z$. |
| **A04** Tham số | [parameter_registry.csv](parameter_registry.csv), [.xlsx](parameter_registry.xlsx), [.json](parameter_registry.json) | 43 mục: nguồn, đơn vị SI, khoảng khảo sát, xuất xứ (provenance) và module. |
| **A05** Pressure | [pressure.py](pressure.py), [contact_patch.png](contact_patch.png) | 3 họ hàm (Uniform, Trapezoid, Quartic), tải không âm, kiểm tra chuẩn hóa tích phân. |
| **A06** Solver | [reference_solver.py](reference_solver.py), [wheel_interface.py](wheel_interface.py) | MoC Semi-Lagrangian float64, sao chép snapshot độc lập, biên nhân quả giữ hằng. |
| **A07** Verification | [reference_tests.py](reference_tests.py), [independent_solver.py](independent_solver.py), [results/](results/) | 14 unit test đạt; hội tụ lưới; kiểm chứng chéo Upwind MOL + SciPy BDF. |
| **A08** Manuscript | [section_II_B.md](section_II_B.md), [section_III_A_physics.md](section_III_A_physics.md), [section_V_A_verification.md](section_V_A_verification.md) | Bản tiếng Anh có trích dẫn nguồn, phương trình khớp 100% với solver. |
| **A09** Tổng hợp | [reference_verification_report.md](reference_verification_report.md), [figures/](figures/) | Số liệu thực nghiệm, thí nghiệm loại trừ (ablations), đối chứng ROM và giới hạn. |
| **A10** Handoff | [README.md](README.md), [data_schema.md](data_schema.md), [datasets/manifest.json](datasets/manifest.json) | Giao diện API, hướng dẫn chạy, schema dữ liệu, mã băm SHA-256 và chính sách split. |

Phần phụ thuộc ngoài gói chưa thể hoàn thành: audit `src/sil/physics.py`, `src/tools/dataset/lugre_ground_truth.py`, tích hợp/duyệt mã xe của Member C; người dùng xác nhận chưa có các tệp này trong workspace và yêu cầu làm phần còn lại. Đã có checklist 7 bước trong [source_audit.md](source_audit.md) và giao diện thay thế trong [wheel_interface.py](wheel_interface.py) để dùng ngay khi code xuất hiện. Tuyệt đối không ghi nhận các phần này là đã kiểm tra thực tế khi chưa có mã nguồn.

## Mô hình và quy ước dấu đã khóa cho gói này

- **Vận tốc trượt cao su tương đối:** $\mathbf{v}_r = (V_x - r\omega, \, V_y)$; lực ma sát tác dụng lên xe có dấu ngược với chiều biến dạng của sợi cao su.
- **Phương trình đạo hàm riêng (PDE):** $\partial_t z_i + a \partial_x z_i = v_{ri} - C_i z_i$; hệ số suy giảm $C_i(s) = \sigma_{0i} s / g(s)$ sử dụng chuẩn vận tốc trượt chung của cả hai trục $s = \|\mathbf{v}_r\|_2$.
- **Áp suất tiếp xúc:** Là mật độ tải đường pháp tuyến $p(x)$ theo đơn vị $\text{N/m}$, đóng vai trò trọng số phân bố lực khi động học đã được áp đặt trước ($\int_0^L p(x) \, dx = F_z$).
- **Mô-men tự định hướng:** $M_z = \int_0^L (L/2 - x) q_y(x) \, dx$ sử dụng cánh tay đòn $X = L/2 - x$.
- **Miền hợp lệ:** Tải trọng đứng $F_z > 0$, chiều quay tiến $\omega \ge 0$; giao diện quay bánh xe yêu cầu $\omega > 0$ và ném lỗi rõ ràng trước biến cố khóa bánh/dừng xe ($\omega \le 0$).
- **Không cắt xén nhân tạo:** Tuyệt đối không áp đặt force clipping hay saturation nhân tạo lên phương trình vật lý.

Gói mô tả quyết định triển khai chính thức của Member A, chưa giả định các thành viên còn lại hoặc giảng viên đã duyệt. Mọi thay đổi về quy ước này bắt buộc phải sửa đồng thời model spec, test suite và phiên bản schema.

## Hướng dẫn cho Member B (PINN & Surrogate Models)

- Sử dụng [`pilot_reference.npz`](pilot_reference.npz) để phát triển biểu diễn trường biến dạng/bộ nhớ và dự đoán chuỗi động học dưới kích thích áp đặt; bắt buộc phải cấp các hệ số dạng sóng kích thích tương lai làm đầu vào khi mạng dự đoán tương lai.
- Sử dụng [`datasets/candidate_reference.npz`](datasets/candidate_reference.npz) cho giao diện phanh một bước. Đọc kỹ hợp đồng dữ liệu trong [`data_schema.md`](data_schema.md); metadata lưu trữ đầy đủ điều kiện biên, thông tin ứng viên và cờ kiểm tra chất lượng.
- Quy mô pilot gồm 24 chuỗi động học và 36 ví dụ ứng viên; không tự tuyên bố là đã đủ dữ liệu cho huấn luyện OOD tổng quát hóa lốp mới. Giữ nguyên phân chia train/val/test theo trajectory trước khi cắt sliding windows; tuyệt đối không đưa $\omega$ tương lai hoặc lực tương lai của plant vào đặc trưng đầu vào mạng.
- Mô hình tham chiếu REF đã được kiểm chứng số học trong ca chạy; mô hình thu gọn ROM hai trạng thái có cấu hình tại [`rom_calibration.json`](rom_calibration.json); gói này chưa chứa trọng số mạng PINN.

## Hướng dẫn cho Member C (Vehicle Dynamics & Braking Control)

- Đọc tài liệu [`member_C_integration.md`](member_C_integration.md) và ví dụ API trong [`README.md`](README.md). Hàm `reference_step` trong [`wheel_interface.py`](wheel_interface.py) trả về mảng mẫu lực theo thời gian, trạng thái lốp kế tiếp $z_{next}$, xung lực tích phân $\int \mathbf{F} \, dt$, tốc độ góc $\omega$, trạng thái cơ cấu phanh và nhật ký chẩn đoán.
- Sao chép cùng một snapshot trạng thái $(\mathbf{z}, \omega, T_b)$ tại thời điểm $t_k$ cho mỗi lệnh phanh ứng viên; chỉ commit trạng thái kế tiếp cho lệnh phanh thực tế được áp dụng.
- Các tham số bán kính $r$, quán tính bánh $I_w$ và trễ cơ cấu phanh $\tau_b$ trong registry là thiết kế benchmark, Member C cần thay bằng thông số thực tế của xe nghiên cứu. Không dùng giao diện hiện tại để khẳng định đã mô phỏng dừng xe hoàn toàn, đảo chiều chuyển động hoặc mất tiếp xúc ($F_z \le 0$).

## Hướng dẫn cho Member D (Verification & Quality Audit)

- Chạy kiểm thử tự động bằng lệnh `python run_all.py`, đối chiếu kết quả trong [`results/unit_tests.log`](results/unit_tests.log) (14/14 test pass), các bảng CSV hội tụ (`convergence_space.csv`, `convergence_time.csv`, `wheel_convergence.csv`), bảng so sánh solver độc lập [`results/independent_comparison.csv`](results/independent_comparison.csv) và kiểm tra chất lượng dataset [`datasets/quality_checks.json`](datasets/quality_checks.json).
- Toàn bộ ngưỡng nghiệm thu pilot (`force_gate < 0.02`, `state_gate < 0.03`) đã được khóa cố định trong registry trước khi chạy thí nghiệm.
- Đọc kỹ phân định 4 cấp độ bằng chứng $G0/G1/G2/G3$ trong [`reference_verification_report.md`](reference_verification_report.md); lưu ý mức $G2$ chỉ tái dựng điều kiện mô phỏng Hình 4 (Deur) và còn thiếu sai số số hóa đồ thị gốc; mức $G3$ hiện chưa có dữ liệu đo thực nghiệm. Member D cần kiểm tra độc lập và thiết lập các cổng nghiệm thu phù hợp khi mạng PINN báo cáo cải thiện nhỏ.

## Những điều nhóm được phép giả định

- Toàn bộ dữ liệu tuân thủ chuẩn đơn vị SI, kiểu dữ liệu số thực `float64`, các tệp đều đã được kiểm tra tính hữu hạn (không NaN/Inf), kiểm tra mã băm SHA-256 và không rò rỉ dữ liệu phân chia nhóm như công bố trong [`results/delivery_validation.json`](results/delivery_validation.json).
- Điều kiện đầu $z_0$ được bảo toàn và cập nhật xuyên suốt thời gian, không bị reset ngầm.
- Thuật toán chuẩn hóa áp suất sử dụng cùng hệ trọng số tích phân hình thang như phép tích phân lực tiếp tuyến.
- Mọi chuỗi dữ liệu trong dataset phát hành đều đã được đối chiếu đạt chuẩn sai số so với lưới không gian và bước thời gian mịn gấp đôi.
- **Bản chất dữ liệu:** Dữ liệu là nghiệm số tham chiếu (*numerical reference*), không phải dữ liệu đo đạc thực nghiệm lốp thật (*measured ground truth*). Không có bảo đảm lý thuyết về an toàn đóng vòng hoặc thời gian đáp ứng thời gian thực trên MCU. Thành viên D và nhóm cần đọc các con số định lượng cụ thể trong báo cáo thay vì chỉ suy diễn từ nhãn PASS định tính.
