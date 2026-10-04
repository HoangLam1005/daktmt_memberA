# Hợp đồng dữ liệu bàn giao A → B/C/D

Đọc `model_spec.md` trước. Tất cả float64, SI, thứ tự thành phần [x,y]. NPZ đọc bằng `numpy.load(..., allow_pickle=False)`. Không có Python object pickle.

## pilot_reference.npz — kinematic trajectories

| Key | Shape | Đơn vị/ý nghĩa |
|---|---|---|
| t | (T,) | s, lưới thời gian chung |
| grid_m, integration_weights | (Nx,) | m, nút và trọng số hình thang |
| z | (K,T,Nx,2) | m, toàn bộ lịch sử trường bristle |
| force | (K,T,2) | N, lực lên bánh/xe |
| Mz | (K,T) | N m, moment theo A8 |
| vr | (K,T,2) | m/s, đầu vào slip được áp đặt |
| transport_speed, Fz | (K,) | m/s, N, hằng trong mỗi chuỗi |
| pressure_family | (K,) | uniform / trapezoid / quartic |
| trajectory_id, split | (K,) | nhóm và train/validation/test |
| parameter_set_id, solver_version | scalar strings | định danh |

24 chuỗi độc lập, 16 train/4 validation/4 test; cùng bộ tham số lốp, nên **không** đo khả năng tổng quát sang bộ lốp mới. `datasets/kinematic_configs.json` chứa seed-derived amplitudes, tần số, pha, shape và tải. Nếu B dự đoán tương lai của các chuỗi này, phải nhận luật kích thích/các hệ số tương đương làm input. Chỉ cung cấp hiện tại rồi yêu cầu đoán sin tương lai sẽ làm sai hợp đồng nhân quả. Đây là pilot, không phải bộ train PINN đầy đủ đã được B thiết kế.

## datasets/candidate_reference.npz — một bước ứng viên phanh

36 ví dụ từ 12 snapshot độc lập, mỗi snapshot có 3 lệnh. Tất cả sibling candidates ở cùng split: 24 train/6 validation/6 test. `trajectory_id` là nhóm snapshot, không hàm ý đã có rollout xe dài.

| Key | Shape | Ý nghĩa |
|---|---|---|
| tau_queries | (Q,) | thời gian tương đối trong horizon |
| z0, z_next | (N,Nx,2) | trạng thái đầu/cuối |
| force | (N,Q,2) | lực từng thời điểm |
| omega, applied_brake_torque | (N,Q) | rad/s, N m |
| force_impulse | (N,2) | N s, tổng midpoint từng bước con |
| metadata_json | scalar Unicode | JSON list, cùng thứ tự ví dụ |
| split, trajectory_id | (N,) | nhóm, không chia candidates anh em |
| grid_m, integration_weights | (Nx,) | nút/trọng số |

Metadata cũng ở `datasets/candidate_metadata.json`: Vx,Vy,Fz,shape,omega0,Tb0,Tcmd,t0,dt_control,horizon,forecast_model,clamp_events,out_of_domain và lỗi đối chiếu lưới mịn. Đầu vào là thông tin lý tưởng biết trước tại t0, không gắn nhãn measured. Không dùng omega tương lai/force tương lai trong input predictor.

`datasets/quality_checks.json` ghi gate từng chuỗi. `datasets/manifest.json` lưu SHA256, seed, phiên bản, initialization và mức bằng chứng. Nhãn `verified_reference` chỉ nghĩa kiểm chứng số G0/G1 trên miền pilot, không chứng nhận thực nghiệm hay đã được D duyệt.

## Quy tắc dùng

Chia theo trajectory trước khi cắt windows; mọi warm-up và candidate của cùng snapshot ở cùng nhóm. Chỉ fit normalization/PCA/ROM/mạng bằng train; validation cho lựa chọn, test chỉ chấm. Family ID duy nhất theo realization không có nghĩa family-OOD; các split hiện cùng họ sóng và cùng tham số. B phải tạo partition khác nếu muốn tuyên bố OOD.

Ở xe bốn bánh, C quản lý thứ tự FL/FR/RL/RR, pose, yaw và tải; interface A là một bánh. Sao chép snapshot cho mỗi lệnh rồi commit trạng thái theo lệnh thật. Ngoài miền thì bắt exception và quyết định ở controller, không thay nhãn lỗi bằng nội suy.
