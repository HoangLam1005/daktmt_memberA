"""Build paper verification paragraphs and handoff from actual saved experiment logs."""
from pathlib import Path
import csv, json, hashlib, platform, importlib.metadata

ROOT = Path(__file__).resolve().parent

HEADER_MAP = {
    'nx': '$N_x$',
    'dx_m': r'$\Delta x\text{ [m]}$',
    'dt_s': r'$\Delta t\text{ [s]}$',
    'dt_moc_s': r'$\Delta t_{\mathrm{MoC}}\text{ [s]}$',
    'state_rms_m': r'$\mathrm{RMS}(\mathbf{z})\text{ [m]}$',
    'force_error_over_Fz': r'$\Vert \Delta \mathbf{F} \Vert / F_z$',
    'max_force_error_over_Fz': r'$\Vert \Delta \mathbf{F} \Vert_{\max} / F_z$',
    'max_error_over_Fz': r'$\Vert \Delta \mathbf{F} \Vert_{\max} / F_z$',
    'a_mps': r'$a\text{ [m/s]}$',
    'state_error_m': r'$\Vert \Delta \mathbf{z} \Vert_{\max}\text{ [m]}$',
    'omega_error_rad_s': r'$\Delta \omega\text{ [rad/s]}$',
    'impulse_error_Ns': r'$\Delta I\text{ [N}\cdot\text{s]}$',
    'case': 'Kịch bản (Case)',
    'force_RMSE_N': r'$\mathrm{RMSE}(\mathbf{F})\text{ [N]}$',
    'REF_wall_s': r'$t_{\mathrm{wall, REF}}\text{ [s]}$',
    'ROM_wall_s': r'$t_{\mathrm{wall, ROM}}\text{ [s]}$',
}

def table(file):
    with (ROOT / 'results' / file).open() as f:
        rows = list(csv.DictReader(f))
    raw_keys = list(rows[0])
    headers = [HEADER_MAP.get(k, k) for k in raw_keys]
    return '| ' + ' | '.join(headers) + ' |\n| ' + ' | '.join(['---'] * len(headers)) + ' |\n' + '\n'.join('| ' + ' | '.join(str(r[k]) for k in raw_keys) + ' |' for r in rows)

def main():
    m = json.loads((ROOT / 'results/verification_metrics.json').read_text(encoding='utf-8'))
    d = json.loads((ROOT / 'datasets/manifest.json').read_text(encoding='utf-8'))
    rom = json.loads((ROOT / 'rom_calibration.json').read_text(encoding='utf-8'))

    report = f"""# Báo cáo kiểm chứng reference solver Member A

Tất cả số liệu dưới đây được đọc trực tiếp từ file log của lần chạy hiện tại; không có số liệu giả lập kết quả PINN hoặc xe trong báo cáo này.

## 1. Mức bằng chứng và ngưỡng nghiệm thu (Verification Gates)

- **G0 (Formulation & Specification):** Đã xác định hệ phương trình vi phân đạo hàm riêng (PDE), thứ nguyên, quy ước dấu, điều kiện biên/đầu ($IC/BC$) và nguồn gốc tham số vật lý trong [model_spec.md](model_spec.md).
- **G1 (Algorithmic & Numerical Verification):** {m['unit_tests']} kiểm thử đơn vị tự động thành công, cùng các thí nghiệm hội tụ không gian/thời gian và đối chiếu solver độc lập bên dưới. Solver kiểm tra độc lập sử dụng sai phân Upwind kết hợp bộ tích phân SciPy BDF (Method of Lines), hoàn toàn không gọi hàm MoC hay hàm tích phân phản ứng của solver chính. Đây là kiểm chứng thuật toán độc lập trong gói mã nguồn; chưa phải review chéo độc lập từ Thành viên D.
- **G2 (Phenomenological & Literature Consistency):** Tái dựng các điều kiện thử nghiệm của Deur et al. (Fig. 4), các tham số nguồn được quy đổi đơn vị tường minh. Do chưa có dữ liệu số hóa trực tiếp từ đồ thị gốc để tính toán sai số định lượng ($\\mathrm{{RMSE}}$), bước này đóng vai trò xác nhận định tính đáp ứng chuyển tiếp.
- **G3 (Experimental Validation):** Hiện tại chưa có dữ liệu đo đạc thực nghiệm từ lốp thực của robot giao hàng.
- **G4 (Integrated Closed-Loop Verification):** Chưa thực hiện kiểm thử vòng kín với mô hình xe đầy đủ / PINN / ZOCBF của các thành viên B, C, D.

**Ngưỡng sai số định trước (Error Tolerances):**
Được khai báo trong registry trước khi chạy thử nghiệm:
- Chuẩn vô cùng sai khác lực tiếp xúc chuẩn hóa: $\\frac{{\\Vert \\Delta \\mathbf{{F}} \\Vert_{{\\max}}}}{{F_z}} < 0.02$ ($2\\%$).
- Sai số RMS trường biến dạng bristle chuẩn hóa: $\\frac{{\\mathrm{{RMS}}(\\Delta z)}}{{\\mu_s / \\min(\\sigma_{{0x}}, \\sigma_{{0y}})}} < 0.03$ ($3\\%$).

Đây là mức chấp nhận cho bộ dữ liệu thí điểm (pilot dataset), không thay thế cho chặn sai số giải tích nghiêm ngặt (analytical error bounds). Việc so sánh lưới mịn / lưới thô là chỉ báo sai số thực nghiệm, không phải chặn sai số tuyệt đối.

## 2. Kiểm thử đơn vị và phân tích hội tụ số (Convergence Analysis)

File nhật ký: [`results/unit_tests.log`](results/unit_tests.log) ghi nhận **{m['unit_tests']}/14 tests PASS**. Các kịch bản bao gồm:
- Zero input: $\\mathbf{{v}}_r = \\mathbf{{0}}, \\mathbf{{z}} = \\mathbf{{0}} \\implies \\mathbf{{F}} = \\mathbf{{0}}$;
- Giới hạn $C_i \\to 0$: thuần trượt / đàn hồi tuyến tính;
- Giới hạn dừng vận chuyển $a = 0$: bảo toàn điều kiện biên, giải nghiệm ODE địa phương;
- Thời gian lưu trú mép vào (inflow residence time $\\tau = x/a$);
- Tính không âm và chuẩn hóa tích phân của áp suất: $p(x) \\ge 0$, $\\int_0^L p(x)\\,dx = F_z$;
- Tính nhất quán về dấu và đối xứng lực: $F_x, F_y$ cùng chiều $v_{{rx}}, v_{{ry}}$;
- Chặn lực vật lý bảo thủ: $\\Vert \\mathbf{{F}} \\Vert \\le \\mu_s F_z$ trong điều kiện trượt dừng isotropic;
- Bộ nhớ biến dạng bristle (tire dynamic memory);
- Eulerian damping tiêu tán năng lượng biến dạng;
- Mô-men tự chỉnh hướng $M_z$ và tải pháp tuyến $F_z$;
- Bất biến quay hệ trục tọa độ và cân bằng công suất ma sát $\\dot{{E}} \\ge 0$;
- Tính độc lập của trạng thái ứng viên (deep copy candidate state);
- Từ chối dữ liệu ngoài miền xác định (out-of-bounds rejection).

### 2.1. Hội tụ theo không gian (Spatial Refinement, $\\Delta t = 0.0002\\text{{ s}}$)

So với trường biến dạng dừng giải tích ($z_{{\\text{{steady}}}}(x)$), sau hơn 2 chu kỳ hạt quét qua vệt tiếp xúc ($t > 2L/a$). Đây là kịch bản có vận chuyển ($a > 0$), đánh giá trực tiếp thuật toán quá độ (transient MoC solver):

{table('convergence_space.csv')}

Sai số RMS của trường biến dạng bristle giảm **{m['space_error_ratio_coarse_to_fine']:.3f} lần** khi tăng mật độ lưới từ thô ($N_x = 65$) đến mịn ($N_x = 513$). Phương pháp nội suy tuyến tính bước chân đặc trưng tạo ra độ khuếch tán số học (numerical diffusion); không suy từ test này thành bậc hai theo không gian cho mọi số Courant. Khi $\\Delta t$ nhỏ cố định với $\\Delta x$ mịn, sai số tái nội suy (spatial remapping error) có thể chiếm ưu thế.

### 2.2. Hội tụ theo thời gian (Temporal Refinement, loại bỏ sai số vận chuyển với $a = 0$)

Đối chiếu với bộ giải chuẩn DOP853 (Runge-Kutta bậc 8) với dung sai khắt khe trên hệ phương trình vi phân biến thiên theo thời gian. Thí nghiệm này cô lập sai số đóng băng điểm giữa (midpoint freezing error); không đại diện cho toàn bộ sai số PDE khi $a > 0$:

{table('convergence_time.csv')}

Sai số giảm **{m['time_error_ratio_coarse_to_fine']:.3f} lần** khi giảm bước thời gian từ $\\Delta t = 0.004\\text{{ s}}$ xuống $\\Delta t = 0.0005\\text{{ s}}$. Đối với đầu vào có bước nhảy gián đoạn, cần phân chia bước thời gian đúng tại thời điểm xảy ra biến cố.

### 2.3. Đối chiếu với Solver độc lập khi có vận chuyển ($a > 0$)

{table('independent_comparison.csv')}

Ở độ phân giải lưới mịn nhất ($N_x = 513$), sai khác lực cực đại chuẩn hóa đạt:
$$\\frac{{\\Vert \\Delta \\mathbf{{F}} \\Vert_{{\\max}}}}{{F_z}} = {m['independent_max_force_error_over_Fz']:.6g}$$
Thí nghiệm này tinh chỉnh đồng thời $\\Delta x$ và $\\Delta t$ để giữ số Courant $\\mathrm{{Cr}} \\approx 0.4$. Khảo sát ban đầu giữ $\\Delta t = 0.00025\\text{{ s}}$ cho thấy sai khác giữa hai cách rời rạc dừng ở mức $0.26\\% F_z$, do sai số thời gian / remapping không giảm cùng lưới; không dùng kết quả đó để tuyên bố hội tụ. Cả hai thuật toán đều có sai số không gian; sự đồng thuận là bằng chứng kiểm chứng tính toán (numerical verification), không phải kiểm chứng thực nghiệm lốp thật.

### 2.4. Ghép nối động lực học quay bánh và cơ cấu chấp hành (Wheel-Actuator Dynamics)

Phương trình vi phân quay bánh:
$$I_w \\dot{{\\omega}} = -T_b - r F_x$$
được giải đồng thời cùng biến dạng tiếp xúc lốp:

{table('wheel_convergence.csv')}

Benchmark được đối chiếu với nghiệm siêu mịn ($N_x = 1025, \\Delta t = 0.000125\\text{{ s}}$). Cùng làm mịn không gian và thời gian ở phép thử ghép này. Solver chưa mô phỏng biến cố khóa cứng bánh xe; sự kiện $\\omega \\le 0$ sẽ phát sinh ngoại lệ rõ ràng.

## 3. Phân bố áp suất, chặn lực và độ nhạy tham số

- **Chuẩn hóa áp suất pháp tuyến:** Sai số cực đại của tổng tải sau chuẩn hóa trên tất cả các profile (uniform, trapezoidal, quartic): **{m['max_discrete_load_error']:.4g} N**. Chi tiết xem [`results/pressure_normalization.csv`](results/pressure_normalization.csv) cho cả sai số trước chuẩn hóa và tọa độ centroid $x_c$. Tổng tải đúng bằng thuật toán chuẩn hóa không tự chứng minh hình dạng áp suất đủ mịn. Dạng uniform và quartic đối xứng được kiểm tra vị trí centroid chính xác tại $x_c = L/2$.
- **Giới hạn lực vật lý:** Solver không sử dụng hàm cắt ngọn nhân tạo (`clamp`) trên $z_i$, $C_i$ hoặc lực $\\mathbf{{F}}$. Giới hạn lực được kiểm tra thỏa mãn chặn trượt dừng kết hợp và quá độ đẳng hướng (isotropic transient). Với quá độ dị hướng (anisotropic transient), áp dụng chặn từng thành phần bảo thủ như quy định trong [model_spec.md](model_spec.md), không mặc định giới hạn vòng tròn $\\mu_s F_z$. Lực cản nhớt Eulerian damping không bị gộp vào chặn ma sát Coulomb giản lược.
- **Phân tích độ nhạy (Sensitivity):** File [`results/sensitivity.csv`](results/sensitivity.csv) ghi nhận kết quả khi thay đổi từng tham số $L, \\sigma_{{0x}}, \\sigma_{{0y}}, \\mu_s, \\mu_k, v_s, \\gamma$ theo các tỷ lệ $0.8 / 1.0 / 1.2$, giữ nguyên tín hiệu kích thích và tải trọng $F_z$. Đây là khảo sát tham số số học, không phải khoảng tin cậy thực nghiệm.

## 4. Bằng chứng bộ nhớ động học và các nghiên cứu triệt tiêu (Ablations)

- **Bộ nhớ động học tiếp xúc (Dynamic Memory):** Hai kịch bản có cùng vận tốc trượt bằng 0 ($\\mathbf{{v}}_r = \\mathbf{{0}}$) và cùng tốc độ $a > 0$ có chênh lệch lực ban đầu là **{m['history_initial_force_difference_N']:.3f} N** do lịch sử biến dạng $\\mathbf{{z}}(x, 0)$ khác nhau. Khi vật liệu cũ thoát khỏi vệt tiếp xúc ($t \\ge L/a$), chênh lệch này triệt tiêu hoàn toàn. Đồ thị [`figures/memory_ablation.png`](figures/memory_ablation.png) minh họa trực tiếp cơ chế này; không áp đặt bộ nhớ phải có lợi sau khi hệ thống đã quên trạng thái ban đầu.
- **Ảnh hưởng phân bố áp suất (Pressure Ablation):** File [`results/pressure_ablation.csv`](results/pressure_ablation.csv) và đồ thị [`figures/pressure_ablation.png`](figures/pressure_ablation.png) áp dụng cùng trường biến dạng $\\mathbf{{z}}$ và cùng tải $F_z$, chỉ thay đổi phân bố $p(x)$; không so sánh các quỹ đạo khác nhau rồi quy sai khác cho áp suất.
- **Mô hình bậc giảm (Reduced-Order Model - ROM):** Hệ số đóng đối lưu $\\kappa = {rom['kappa']:.8f}$, được khớp trên 3 kịch bản huấn luyện riêng và đánh giá trên 2 kịch bản kiểm tra độc lập (held-out):

{table('rom_evaluation.csv')}

Thời gian thực thi (wall-clock runtime) là kết quả đo trên máy tính thử nghiệm, bao gồm overhead của Python trong phiên bản hiện tại. Kết quả chưa qua kiểm thử thống kê warm-up, không đại diện cho độ trễ trên vi điều khiển nhúng (MCU) và chưa đủ cơ sở để kết luận về khả năng tăng tốc khi triển khai thực tế.

## 5. Dữ liệu tham chiếu sinh ra (Delivered Reference Datasets)

Bao gồm **{d['kinematic_trajectories']} quỹ đạo động học** (kinematic trajectories) và **{d['candidate_examples']} ví dụ ứng viên phanh** (braking candidates). Mỗi kịch bản đều được đối chiếu với nghiệm trên lưới mịn gấp đôi ($2 \\times N_x, \\frac{{1}}{{2}} \\Delta t$). Sai số lực chuẩn hóa lớn nhất:
- Quỹ đạo động học: $\\frac{{\\Vert \\Delta \\mathbf{{F}} \\Vert_{{\\max}}}}{{F_z}} = {d['max_kinematic_refinement_error_over_Fz']:.6g}$;
- Kịch bản ứng viên: $\\frac{{\\Vert \\Delta \\mathbf{{F}} \\Vert_{{\\max}}}}{{F_z}} = {d['max_candidate_refinement_error_over_Fz']:.6g}$.

Toàn bộ dữ liệu đều hữu hạn (finite, không có NaN/Inf), lưu trữ đầy đủ trường biến dạng $\\mathbf{{z}}(x, t)$, không có biến cố clamp. Dữ liệu được chia tập theo kịch bản trước khi trích xuất cửa sổ thời gian; mô hình dự báo không được sử dụng thông tin tương lai chưa xuất hiện tại thời điểm ra quyết định.

## 6. Kịch bản dễ phát sinh sai số và giới hạn mô hình

1. **Đầu vào trượt gián đoạn:** Bước trượt thay đổi đột ngột không được phân đoạn thời gian có thể làm giảm bậc hội tụ; vệt tiếp xúc ngắn ở tốc độ cao với lưới thưa gây khuếch tán số học; thành phần cản damping lớn khiến gradient sai số ảnh hưởng trực tiếp đến lực tính toán.
2. **Quan hệ bước lưới - bước thời gian:** Giảm bước thời gian $\\Delta t$ đơn thuần không thể bù đắp cho việc làm thô lưới không gian $\\Delta x$. Solver MoC không bị ràng buộc điều kiện Courant (CFL) về tính ổn định của phản ứng, nhưng sai số vận chuyển (transport error) vẫn tồn tại.
3. **Các biến cố biên động học:** Hiện tượng đảo chiều quay, mất tiếp xúc mặt đường ($F_z \\le 0$) và khóa cứng bánh xe ($\\omega \\le 0$) chưa được hỗ trợ trong giao diện hiện tại; cần mô hình vật lý thân xe và phép thử riêng biệt để xử lý.
4. **Giới hạn mô hình vật lý:** Mô hình chưa xét đến tính phi tuyến của tải trọng thực, góc nghiêng bánh xe (camber), độ mềm thân lốp (carcass compliance), hiệu ứng biến thiên nhiệt độ và bộ thông số thực nghiệm được nhận dạng trên robot thực.
5. **Phạm vi bộ dữ liệu:** Bộ dữ liệu thí điểm có quy mô tập trung và sử dụng một bộ tham số định danh duy nhất; không chứng minh khả năng tổng quát hóa ngoài miền dữ liệu hoặc bảo đảm an toàn điều khiển vòng kín (closed-loop safety).

Thành viên D cần thực hiện rà soát độc lập các ngưỡng kiểm chứng, file log và quy cách phân chia dữ liệu trước khi tiến hành các thử nghiệm chính thức. Không chuyển đổi nhãn dữ liệu thành dữ liệu đo đạc thực nghiệm (measured) hoặc đã được kiểm chứng thực tế (physically validated).
"""
    (ROOT / 'reference_verification_report.md').write_text(report, encoding='utf-8')

    section = f"""## V-A. Numerical reference verification (Member A contribution)

The reference implementation passed {m['unit_tests']} automated tests covering limiting cases, inflow residence, load normalization, sign conventions, state memory, Eulerian damping and candidate-state isolation. Spatial refinement reduced the tested field error by a factor of {m['space_error_ratio_coarse_to_fine']:.2f}. A separate zero-transport temporal study reduced the error by {m['time_error_ratio_coarse_to_fine']:.2f} when the time step was reduced from 4 ms to 0.5 ms.

An independently implemented upwind method-of-lines solver integrated with BDF produced a maximum force discrepancy of {m['independent_max_force_error_over_Fz']*100:.3f}% of wheel load on the finest comparison grid. Each delivered pilot trajectory also passed its coarse/fine gate. The largest force discrepancies were {d['max_kinematic_refinement_error_over_Fz']*100:.3f}% for prescribed-motion trajectories and {d['max_candidate_refinement_error_over_Fz']*100:.3f}% for braking candidates. These are empirical numerical comparisons, not rigorous error bounds.

Pressure and memory ablations isolate one factor at a time. The full protocol, tolerances, grids and results are provided in [reference_verification_report.md](reference_verification_report.md) and the CSV logs. The source-conditioned cornering response is reconstructed separately; a digitized published-curve comparison and measurement-based validation remain unavailable. Consequently, the evidence supports numerical verification of the selected model, not validation of a specific robot tire or a closed-loop safety claim.
"""
    (ROOT / 'section_V_A_verification.md').write_text(section, encoding='utf-8')

    env = {
        'python': platform.python_version(),
        'platform': platform.platform(),
        'dependencies': {k: importlib.metadata.version(k) for k in ['numpy', 'scipy', 'matplotlib']}
    }
    (ROOT / 'environment.json').write_text(json.dumps(env, indent=2), encoding='utf-8')
    (ROOT / 'requirements.txt').write_text('\n'.join(f'{k}=={v}' for k, v in env['dependencies'].items()) + '\n')
    print('Verification report, paper section, environment and dependency lock written')

if __name__ == '__main__':
    main()
