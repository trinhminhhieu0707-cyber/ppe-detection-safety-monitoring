# BÁO CÁO KIỂM ĐỊNH VÀ PHÂN TÍCH CHẤT LƯỢNG DATASET (PHASE 01)
**Dự án:** PPE Detection & Safety Monitoring System  
**Dataset:** Roboflow Universe – Construction Site Safety (Version 30)  
**Ngày thực hiện:** 09/11/2026  
**Kỹ sư thẩm định:** Principal AI Architect & Computer Vision Lead  

---

## 1. TỔNG QUAN VÀ METADATA XÁC MINH (VERIFIED OVERVIEW)

Toàn bộ dữ liệu đã được tải về từ Roboflow Universe API và kiểm tra toàn diện trên ổ cứng cục bộ (`data/raw/`).

| Chỉ số | Giá trị thực tế đã xác minh | Ghi chú kỹ thuật |
| :--- | :--- | :--- |
| **Tổng số hình ảnh** | **717 ảnh** | 100% định dạng JPEG, không có file hỏng (corrupted) |
| **Tập Train** | **521 ảnh** (72.66%) | 487 ảnh có nhãn, 34 ảnh nền không nhãn |
| **Tập Validation** | **114 ảnh** (15.90%) | 104 ảnh có nhãn, 10 ảnh nền không nhãn |
| **Tập Test** | **82 ảnh** (11.44%) | 74 ảnh có nhãn, 8 ảnh nền không nhãn |
| **Ảnh nền (Background / Negative images)** | **52 ảnh** (7.25%) | Tỷ lệ vàng (5–10%) giúp YOLO giảm thiểu False Positive |
| **Tổng số Bounding Box** | **5,570 annotations** | Train: 4,031 \| Valid: 733 \| Test: 806 |
| **Số lượng Class theo `data.yaml`** | **25 classes** | Định dạng chuẩn YOLO: `class_id x_center y_center width height` |
| **Trùng lặp dữ liệu (MD5 Duplicates)** | **0 ảnh trùng lặp** | 717 MD5 hashes hoàn toàn độc lập, **0% Data Leakage** giữa các tập |

---

## 2. BẢNG PHÂN BỐ CHI TIẾT 25 CLASSES (CLASS DISTRIBUTION AUDIT)

| ID | Tên Class | Train | Valid | Test | Tổng số Box | Tỷ lệ (%) | Đánh giá hiện diện trên Test/Val |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **0** | `Excavator` | 145 | 12 | 9 | 166 | 2.98% | Đầy đủ 3 tập |
| **1** | `Gloves` | 231 | 25 | 40 | 296 | 5.31% | Đầy đủ 3 tập (PPE trọng tâm) |
| **2** | `Hardhat` | 385 | 79 | 110 | 574 | 10.31% | Đầy đủ 3 tập (PPE trọng tâm) |
| **3** | `Ladder` | 43 | 10 | 5 | 58 | 1.04% | Đầy đủ 3 tập |
| **4** | `Mask` | 153 | 21 | 28 | 202 | 3.63% | Đầy đủ 3 tập (PPE trọng tâm) |
| **5** | `NO-Hardhat` | 292 | 69 | 41 | 402 | 7.22% | Đầy đủ 3 tập (Vi phạm trọng tâm) |
| **6** | `NO-Mask` | 338 | 74 | 79 | 491 | 8.82% | Đầy đủ 3 tập (Vi phạm trọng tâm) |
| **7** | `NO-Safety Vest`| 386 | 106 | 90 | 582 | 10.45% | Đầy đủ 3 tập (Vi phạm trọng tâm) |
| **8** | `Person` | 808 | 166 | 174 | 1,148 | 20.61% | Đầy đủ 3 tập (Class nền tảng tracking) |
| **9** | `SUV` | 16 | 0 | 0 | 16 | 0.29% | **LỖI: 0 trên Val, 0 trên Test** |
| **10**| `Safety Cone` | 464 | 44 | 92 | 600 | 10.77% | Đầy đủ 3 tập |
| **11**| `Safety Vest` | 322 | 41 | 61 | 424 | 7.61% | Đầy đủ 3 tập (PPE trọng tâm) |
| **12**| `bus` | 1 | 0 | 0 | 1 | 0.02% | **LỖI NGHIÊM TRỌNG: Chỉ 1 box duy nhất** |
| **13**| `dump truck` | 127 | 13 | 17 | 157 | 2.82% | Đầy đủ 3 tập |
| **14**| `fire hydrant` | 6 | 0 | 0 | 6 | 0.11% | **LỖI: 0 trên Val, 0 trên Test** |
| **15**| `machinery` | 31 | 8 | 6 | 45 | 0.81% | Đầy đủ 3 tập |
| **16**| `mini-van` | 6 | 1 | 0 | 7 | 0.13% | **Cảnh báo: 0 trên Test** |
| **17**| `sedan` | 39 | 13 | 2 | 54 | 0.97% | Đầy đủ 3 tập |
| **18**| `semi` | 7 | 0 | 0 | 7 | 0.13% | **LỖI: 0 trên Val, 0 trên Test** |
| **19**| `trailer` | 13 | 1 | 1 | 15 | 0.27% | Đầy đủ 3 tập |
| **20**| `truck` | 29 | 4 | 2 | 35 | 0.63% | Đầy đủ 3 tập |
| **21**| `truck and trailer`| 4 | 3 | 0 | 7 | 0.13% | **Cảnh báo: 0 trên Test** |
| **22**| `van` | 18 | 3 | 7 | 28 | 0.50% | Đầy đủ 3 tập |
| **23**| `vehicle` | 74 | 18 | 30 | 122 | 2.19% | Đầy đủ 3 tập |
| **24**| `wheel loader`| 93 | 22 | 12 | 127 | 2.28% | Đầy đủ 3 tập |

---

## 3. PHÂN TÍCH KÍCH THƯỚC BOUNDING BOX (COCO SCALE DIAGNOSTICS)

Phân bổ diện tích bounding box (tương quan kích thước chuẩn $640 \times 640$):
- **Small Objects** ($Area < 32^2$): **2,190 box (39.32%)**
- **Medium Objects** ($32^2 \le Area \le 96^2$): **1,411 box (25.33%)**
- **Large Objects** ($Area > 96^2$): **1,969 box (35.35%)**

### Tỷ lệ vật thể nhỏ ở các class trọng tâm:
- `Gloves`: **64.2% là vật thể nhỏ** (Small).
- `NO-Mask`: **70.3% là vật thể nhỏ** (Small).
- `Hardhat`: **50.9% là vật thể nhỏ** (Small).
- `Person`: Chỉ có 17.3% Small, 58.0% là Large.

> [!WARNING]
> **Thách thức thị giác máy tính:** Việc hơn 50% đến 70% các nhãn PPE quan trọng (`Hardhat`, `Gloves`, `NO-Mask`) là đối tượng nhỏ (Small Object) đặt ra yêu cầu cao khi chọn mô hình và kích thước đầu vào (Input Resolution `imgsz=640` hoặc `1280` kết hợp P3 feature pyramid ở Phase 02).

---

## 4. QUAN HỆ ĐỒNG XUẤT HIỆN GIỮA PERSON VÀ PPE (CO-OCCURRENCE AUDIT)

- **Tổng số ảnh có annotation:** 665 ảnh.
- **Ảnh có đồng thời `Person` và các trang bị PPE:** **479 ảnh (72.03%)**.
- **Ảnh có `Person` nhưng KHÔNG gắn nhãn PPE:** **36 ảnh (5.41%)** *(Do người đứng quá xa hoặc bị che khuất)*.
- **Ảnh có nhãn PPE nhưng KHÔNG CÓ `Person`:** **6 ảnh (0.90%)** *(Các trường hợp góc chụp cận cảnh đầu/mũ hoặc găng tay đặt trên máy móc)*.

---

## 5. DANH SÁCH LỖI VÀ VẤN ĐỀ PHÁT HIỆN ĐƯỢC (RISK LOG)

1. **Vấn đề Zero-shot Validation/Testing ở nhóm xe cơ giới:**
   - 4 class (`SUV`, `bus`, `fire hydrant`, `semi`) hoàn toàn **không có bất kỳ mẫu nào** trong tập Valid và Test.
   - 2 class (`mini-van`, `truck and trailer`) **không có mẫu** trong tập Test.
   - Hậu quả: Nếu giữ nguyên để huấn luyện 25 classes, các chỉ số mAP50 và mAP50-95 của các class này trên tập Valid/Test sẽ bằng 0 hoặc không xác định (Undefined), kéo tụt mAP chung và làm sai lệch đánh giá mô hình.
2. **Hiện tượng phân rã nhãn thừa (Class Fragmentation):**
   - Các class `truck`, `dump truck`, `semi`, `trailer`, `truck and trailer`, `van`, `mini-van`, `SUV`, `sedan`, `vehicle` bị chia quá nhỏ và chồng chéo về mặt ngữ nghĩa (Semantics). Trong khi đó, mục tiêu cốt lõi của đề tài là **PPE Detection & Safety Monitoring**.
3. **Mất cân bằng dữ liệu cực đoan (Long-tail Imbalance):**
   - Class `bus` chỉ có **1 mẫu**, `semi` có 7 mẫu, so với `Person` có **1,148 mẫu** (chênh lệch hơn 1,000 lần).
4. **Nhãn âm tính (Negative Classes) đòi hỏi logic liên kết chặt chẽ:**
   - Các nhãn `NO-Hardhat` (402), `NO-Safety Vest` (582), `NO-Mask` (491) là dạng nhãn "sự vắng mặt" (Absence of object). Khi triển khai ở Phase 04, nếu một người đứng quay lưng hoặc bị che khuất đầu, mô hình rất dễ gây nhầm lẫn nếu không có Spatial Association với Bounding Box `Person`.

---

## 6. CHIẾN LƯỢC SỬ DỤNG CLASSES ĐƯỢC PHÊ DUYỆT: PHƯƠNG ÁN 1 (CHUYÊN SÂU PPE - 9 CLASSES)

Dự án chính thức phê duyệt và triển khai **Phương án 1: Chuyên sâu Giám sát An toàn Lao động (9 Classes)**.

Đây là lựa chọn chuẩn mực kỹ thuật cao nhất cho một dự án CV chuyên ngành: Loại bỏ triệt để nhóm nhãn xe cộ/máy móc rời rạc và bị lỗi phân bố, tập trung toàn bộ dung lượng mô hình vào bài toán nhận diện con người và trang bị bảo hộ cá nhân:

| Target ID | Tên Class Chuẩn hóa | Train (Box) | Valid (Box) | Test (Box) | Tổng số Box | Hiện diện trên Test | Ý nghĩa an toàn |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **0** | `Person` | 808 | 166 | 174 | **1,148** | ✅ 100% cân đối | Đối tượng trung tâm (Tracking & Association) |
| **1** | `Hardhat` | 385 | 79 | 110 | **574** | ✅ 100% cân đối | Tuân thủ: Mũ bảo hộ |
| **2** | `NO-Hardhat` | 292 | 69 | 41 | **402** | ✅ 100% cân đối | **Vi phạm: Không đội mũ bảo hộ** |
| **3** | `Safety Vest` | 322 | 41 | 61 | **424** | ✅ 100% cân đối | Tuân thủ: Áo phản quang |
| **4** | `NO-Safety Vest` | 386 | 106 | 90 | **582** | ✅ 100% cân đối | **Vi phạm: Không mặc áo phản quang** |
| **5** | `Mask` | 153 | 21 | 28 | **202** | ✅ 100% cân đối | Tuân thủ: Khẩu trang |
| **6** | `NO-Mask` | 338 | 74 | 79 | **491** | ✅ 100% cân đối | **Vi phạm: Không đeo khẩu trang** |
| **7** | `Gloves` | 231 | 25 | 40 | **296** | ✅ 100% cân đối | Tuân thủ: Găng tay bảo hộ |
| **8** | `Safety Cone` | 464 | 44 | 92 | **600** | ✅ 100% cân đối | Cảnh báo: Cọc tiêu vùng nguy hiểm |
| **Tổng** | **9 Classes Cốt lõi** | **3,379** | **625** | **715** | **4,719** | **100% chuẩn mực** | Triệt tiêu hoàn toàn lỗi 0-sample |

### Đánh giá sau chuẩn hóa:
- **Triệt tiêu 100% lỗi Zero-sample:** Không còn bất kỳ class nào bị thiếu mẫu trên tập Test hay Valid.
- **Tận dụng 166 ảnh nền (Background images ~ 23.1%):** Các hình ảnh máy móc, xe cộ, công trường không có người được giữ lại nguyên vẹn và đóng vai trò làm mẫu âm (Negative samples), giúp mô hình YOLO sau này không bị báo động giả (False Alarm) khi nhìn vào vật thể lạ ngoài công trường.
- **Bảo toàn dữ liệu gốc:** Toàn bộ dữ liệu thô ban đầu vẫn nằm nguyên vẹn tại `data/raw/`.

---

## 7. KẾT LUẬN NGHIỆM THU PHASE 01

1. Dữ liệu gốc đã được tải về, giải nén và lưu trữ bất biến tại `data/raw/`.
2. Dữ liệu chuẩn hóa 9 classes PPE đã được xử lý và lưu độc lập tại `data/processed/`.
3. File cấu hình chuẩn hóa [`configs/data_ppe.yaml`](file:///d:/desktop/Năm%204%20kì%201/ppe-detect/ppe-detection-safety-monitoring/configs/data_ppe.yaml) đã sẵn sàng.
4. Đã đối soát 100% bounding box, không có lỗi tọa độ hay data leakage.

👉 **PHASE 01 ĐÃ CHÍNH THỨC HOÀN THÀNH. ĐỦ ĐIỀU KIỆN 100% CHUYỂN SANG PHASE 02.**

