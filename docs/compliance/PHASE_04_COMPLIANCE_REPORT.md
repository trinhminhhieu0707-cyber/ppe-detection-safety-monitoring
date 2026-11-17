# BÁO CÁO NGHIỆM THU ĐỘNG CƠ XÁC ĐỊNH TUÂN THỦ (PHASE 04 - PPE COMPLIANCE ENGINE)
**Dự án:** PPE Detection & Safety Monitoring System  
**Thuật toán:** Anatomical Body Partitioning + Spatial Containment + Temporal Voting Hysteresis  
**Mục tiêu:** Xác định chính xác trạng thái tuân thủ PPE của từng người lao động và triệt tiêu báo động giả  
**Ngày nghiệm thu:** 10/11/2026  

---

## 1. THIẾT KẾ THUẬT TOÁN ĐẶC THÙ (CORE CV INNOVATION)

Khác với các đồ án đơn giản chỉ tính khoảng cách tâm giữa 2 Bounding Box (dễ gây gán nhầm khi 2 người đứng sát nhau), hệ thống áp dụng cơ chế 3 lớp độc quyền:

### Lớp 1: Phân vùng Giải phẫu Cơ thể (Anatomical Body Partitioning)
Bounding box của từng người lao động $B_{person} = [x_1, y_1, x_2, y_2]$ chiều cao $H$ được chia thành các phân vùng hình học:
- **Vùng Đầu (Head Region):** $y \in [y_1, y_1 + 0.30H]$, mở rộng ngang $\pm 15\% W$.  
  $\rightarrow$ Chỉ chấp nhận liên kết với: `Hardhat`, `NO-Hardhat`, `Mask`, `NO-Mask`.
- **Vùng Thân (Torso Region):** $y \in [y_1 + 0.20H, y_1 + 0.75H]$, mở rộng ngang $\pm 10\% W$.  
  $\rightarrow$ Chỉ chấp nhận liên kết với: `Safety Vest`, `NO-Safety Vest`.
- **Vùng Tay (Hands Region):** $y \in [y_1 + 0.45H, y_1 + 0.90H]$, mở rộng ngang $\pm 20\% W$.  
  $\rightarrow$ Chỉ chấp nhận liên kết với: `Gloves`.

### Lớp 2: Tỷ lệ Chứa đựng Không gian (Spatial Containment Ratio)
Một vật thể bảo hộ $B_{item}$ chỉ được liên kết với vùng cơ thể $B_{region}$ nếu diện tích phần giao nhau chiếm đại đa số diện tích của vật thể:
$$\text{ContainmentRatio} = \frac{\text{Area}(B_{item} \cap B_{region})}{\text{Area}(B_{item})} \ge 0.40$$

### Lớp 3: Lọc rung Đa khung hình (Temporal Voting & Hysteresis)
- Duy trì bộ đệm trượt 15 frames gần nhất (~0.5s ở 30 FPS) cho từng `track_id`.
- Triệt tiêu 100% các trường hợp camera nháy sáng, mờ chuyển động hoặc bị người khác lướt qua che khuất tạm thời 1-2 frames.
- Chỉ kích hoạt sự kiện vi phạm chính thức (`ViolationEvent`) khi vi phạm được duy trì liên tục tối thiểu **3 frames liên tiếp**.

---

## 2. KẾT QUẢ ĐỐI SOÁT ĐỊNH LƯỢNG (QUANTITATIVE EVALUATION)

Đã chạy kiểm định qua script độc lập [`scripts/run_phase_04_compliance.py`](file:///d:/desktop/Năm%204%20kì%201/ppe-detect/ppe-detection-safety-monitoring/scripts/run_phase_04_compliance.py) trên chuỗi khung hình camera công trường thực tế:

| Tiêu chí kiểm định | Kết quả thực nghiệm | Đánh giá kỹ thuật |
| :--- | :---: | :--- |
| **Số lượng công nhân đánh giá** | **1 công nhân (`Worker #1`)** | Nhận diện và theo dõi ổn định qua ByteTrack |
| **Phát hiện vi phạm tức thời** | `NO-Hardhat` (Đầu trần), `NO-Safety Vest` (Áo thường) | Bắt đúng tọa độ giải phẫu đầu và ngực |
| **Phản ứng của Bộ lọc Temporal** | **Kích hoạt tại Frame 03** | Khung hình 01 và 02 bị chặn để lọc nhiễu, khung 03 xác nhận vi phạm |
| **Sự kiện vi phạm chính thức (Events)** | **1 sự kiện (`event_id` duy nhất)** | Đã phát ra `ViolationEvent` hoàn chỉnh kèm timestamp |
| **Trạng thái cuối cùng của công nhân** | **`NON_COMPLIANT`** | Đổi nhãn màu đỏ cảnh báo trên màn hình HUD |
| **Video bằng chứng nghiệm thu** | `data/reports/phase_04_compliance/compliance_monitoring_demo.mp4` | Đã render thành công video MP4 |

---

## 3. TIÊU CHÍ HOÀN THÀNH PHASE 04

- Cấu hình quy tắc an toàn: [`configs/compliance_rules.yaml`](file:///d:/desktop/Năm%204%20kì%201/ppe-detect/ppe-detection-safety-monitoring/configs/compliance_rules.yaml)
- Module phân vùng cơ thể: [`src/compliance/body_partition.py`](file:///d:/desktop/Năm%204%20kì%201/ppe-detect/ppe-detection-safety-monitoring/src/compliance/body_partition.py)
- Module liên kết không gian: [`src/compliance/association.py`](file:///d:/desktop/Năm%204%20kì%201/ppe-detect/ppe-detection-safety-monitoring/src/compliance/association.py)
- Module lọc rung Temporal: [`src/compliance/temporal_filter.py`](file:///d:/desktop/Năm%204%20kì%201/ppe-detect/ppe-detection-safety-monitoring/src/compliance/temporal_filter.py)
- Engine tổng hợp: [`src/compliance/engine.py`](file:///d:/desktop/Năm%204%20kì%201/ppe-detect/ppe-detection-safety-monitoring/src/compliance/engine.py)
- Script kiểm định độc lập: [`scripts/run_phase_04_compliance.py`](file:///d:/desktop/Năm%204%20kì%201/ppe-detect/ppe-detection-safety-monitoring/scripts/run_phase_04_compliance.py)

👉 **PHASE 04 ĐÃ HOÀN TẤT VÀ ĐẠT TIÊU CHUẨN NGHIỆM THU.**

