# Nguồn, lựa chọn mô hình và phần chưa thể audit

| Nguồn | Vị trí dùng | Quyết định |
|---|---|---|
| [S1 Deur 2002](https://skoge.folk.ntnu.no/prost/proceedings/ifac2002/data/content/00284/284.pdf) | §2, Appendix B, Fig.4 | Bộ số lốp, shape hình thang, ca kích thích tái dựng |
| [S2 Tsiotras et al.](https://dcsl.gatech.edu/papers/vsd04R.pdf) | §2 Eqs.1–8; §3.1; §5.1 | Cấu trúc chuẩn hóa, MoC, đối chứng closure |
| [S3 thử nghiệm dọc](https://dcsl.gatech.edu/papers/iasted02b.pdf) | Table 2, §4 | Không đưa bộ tham số này vào dataset; khác lốp/ca thử, chưa có chuỗi đo gốc |

Ba họ pressure đã thực thi. Quartic trong gói là đa thức đối xứng được chọn để kiểm tra, không tái nhận dạng empirical pressure. ROM dùng closure hằng tối ưu bằng dữ liệu train; không gắn nhãn exact aggregate dynamics vì không lưu hệ moments và lịch sử thoát vệt như nguồn.

Ca Fig.4 được dựng với tốc độ 20/60 km/h, góc 0→1° tại 0.05 s, pure cornering và tham số nguồn. Kết quả xuất riêng; không có đường digitized và sai số digitization, nên G2 chỉ hoàn thành phần tái dựng điều kiện và nghiệm, chưa kết luận khớp định lượng hình công bố. G3 chưa có dữ liệu đo. Đây là giới hạn bằng chứng, không được thay bằng nhãn PASS giả.

## Mã dự án chưa tồn tại trong đầu vào

Người dùng xác nhận chưa có `src/sil/physics.py`, `src/tools/dataset/lugre_ground_truth.py` và mã xe Member C. Theo yêu cầu tiếp tục phần còn lại, không dựng một báo cáo đã audit các tệp không có.

Khi mã có sẵn, đối chiếu theo checklist cụ thể:

1. Kiểm tra `vr`, hệ lực thân/bánh và moment phản lực (-rF_x).
2. Kiểm tra g không thứ nguyên, sigma0 chuẩn hóa và C dùng norm của cả hai trục.
3. Kiểm tra damping dùng partial_t, không phải material derivative.
4. Tìm mọi `clip`, saturation, epsilon trong nguồn, C, z, force; phân biệt giới hạn actuator với sửa vật lý.
5. Kiểm tra p [N/m], tải tích phân, vị trí tâm áp suất và moment.
6. Kiểm tra giữ state xuyên frame và không làm biến đổi snapshot khi thử candidates.
7. Chạy regression cùng ca ở package này; ghi hash/version và sai khác.

## Duyệt vật lý giao diện C hiện có ở mức đặc tả

Tài liệu C phù hợp khi dùng `wheel_to_body` và wheel moment như `model_spec.md`. Đã có test quay hệ bảo toàn tích vô hướng lực–vận tốc, dấu phanh, lực phản hồi quay bánh và không phụ thuộc thứ tự candidate. Chưa kiểm tra đối xứng xe, tải động, 4 kênh actuator hoặc ZOCBF vì chưa có code C. Không có thao tác gửi báo cáo ra ngoài nhóm/chat.
