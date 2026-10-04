# Giao diện lực lốp dành cho Member C

1. **Vận tốc tâm bánh xe theo hệ thân xe:**
   Với bánh xe đặt tại tọa độ $(x_w, y_w)$, tính vận tốc tâm bánh theo hệ thân xe:
   $$
   \mathbf{v}_{w,\text{body}} = \begin{bmatrix} V_x - \dot{\psi} y_w \\ V_y + \dot{\psi} x_w \end{bmatrix}
   $$
   với $\dot{\psi}$ là tốc độ xoay thân xe (*yaw rate*). Sau đó quay theo góc đánh lái $R(-\delta)$ về hệ tọa độ bánh xe. Hàm `wheel_velocity` trong [`wheel_interface.py`](wheel_interface.py) thực hiện phép biến đổi này:
   $$
   \mathbf{v}_w = R(-\delta) \mathbf{v}_{w,\text{body}}
   $$

2. **Vận tốc trượt cao su và vận tốc vận chuyển:**
   Vận tốc trượt tương đối tại vệt tiếp xúc:
   $$
   \mathbf{v}_r = (V_{xw} - r\omega, \, V_{yw})
   $$
   Gọi tire solver với vận tốc vận chuyển $a = |r\omega|$ trong miền quay tiến ($r\omega \ge 0$).

3. **Chuyển đổi lực và mô-men xoay tác dụng lên thân xe:**
   Lực xuất ra từ solver tác dụng lên bánh/xe. Quay lực sang hệ tọa độ thân xe thông qua hàm `wheel_to_body(force, delta)`:
   $$
   \mathbf{F}_b = R(\delta) \mathbf{F}_w
   $$
   Cộng lực $\mathbf{F}_b$ vào thân xe và tính mô-men xoay quanh trọng tâm xe (*yaw moment*):
   $$
   M_{z,\text{total}} = x_w F_{by} - y_w F_{bx} + M_z
   $$
   với $M_z$ là mô-men tự định hướng (*aligning moment*) từ lốp.

4. **Phản lực lên chuyển động quay bánh xe và bảo toàn công suất:**
   Phản lực tiếp tuyến tác dụng lên phương trình quay của bánh xe là $-r F_{xw}$. Mô-men phanh dương $T_b > 0$ chống lại chiều quay $\omega > 0$. Kiểm tra đẳng thức bảo toàn công suất tức thời:
   $$
   F_{xw} V_{xw} + F_{yw} V_{yw} + (-r F_{xw})\omega = \mathbf{F}_w \cdot \mathbf{v}_r
   $$

5. **Phương thức tích hợp điều khiển:**
   Member C có thể sử dụng riêng `ReferenceSolver.step` trong mô hình mô phỏng xe bước nhỏ (*plant simulation*), hoặc sử dụng hàm `reference_step` để đánh giá tập ứng viên phanh (*candidates*) dưới điều kiện biên giữ hằng trong khoảng dự đoán (*horizon*). Trạng thái biến dạng lốp đầu vào $\mathbf{z}$ được sao chép độc lập, không bị thay đổi (*non-mutating*).

6. **Miền giới hạn vật lý và biến cố dừng xe:**
   Tải trọng đứng $F_z \le 0$ (mất tiếp xúc) hoặc tốc độ góc $\omega \le 0$ (khóa bánh / đảo chiều) là nằm ngoài miền vật lý đã chốt của solver. Tuyệt đối không tự ý kẹp cắt (*clamping*) rồi coi là mô hình đã kiểm chứng. Mô hình bánh xe khóa/dừng hẳn phải là phần mở rộng tường minh ở tầng mô hình động lực học xe của Member C.

7. **Xử lý mô-men tự định hướng $M_z$:**
   Lưu giá trị $M_z$ thô nếu Member C quyết định bỏ qua mô-men tự định hướng trong mô hình xe; ghi rõ thí nghiệm loại trừ (*ablation*) đó vào báo cáo. Không cộng thành phần mô-men cản lăn (*rolling resistance*) vào $M_z$.

---

**Kiểm tra đã có:** Chiều dấu phản lực bánh xe, đẳng thức bảo toàn công suất, phép quay tọa độ thân-bánh, tính độc lập khi thử nhiều ứng viên phanh, và độ hội tụ khi làm mịn lưới. 

**Phần chờ tích hợp khi có mã nguồn xe của Member C:** Mô hình động lực học 4 bánh đối xứng, tải trọng động và cân bằng mô-men 3D, cơ cấu chấp hành riêng từng bánh, xử lý trạng thái dừng xe/khóa bánh, và thử nghiệm điều khiển đóng vòng (*closed-loop*). Các hằng số $r, I_w, \tau_b, T_{\max}$ trong registry chỉ là giá trị benchmark; Member C cần thay thế bằng bộ tham số thực tế có nguồn của xe nghiên cứu.
