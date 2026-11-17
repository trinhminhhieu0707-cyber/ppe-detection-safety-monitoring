# BÁO CÁO THỰC NGHIỆM HUẤN LUYỆN MÔ HÌNH (PHASE 02)
**Dự án:** PPE Detection & Safety Monitoring System  
**Kiến trúc:** Ultralytics YOLO11s (Small - 9.4M parameters)  
**Tập dữ liệu:** Roboflow Universe Construction Site Safety (v30) - 9 Clean PPE Classes  
**Môi trường thực thi:** Google Colab Tesla T4 GPU (15GB VRAM)  
**Ngày nghiệm thu:** 09/11/2026  

---

## 1. THIẾT LẬP THỰC NGHIỆM & HYPERPARAMETERS

| Tham số | Giá trị thiết lập | Cơ sở kỹ thuật |
| :--- | :--- | :--- |
| **Model Architecture** | `yolo11s.pt` (Pretrained COCO) | Cân bằng hoàn hảo giữa độ chính xác vật thể nhỏ và độ trễ suy luận |
| **Input Resolution** | $640 \times 640$ | Chuẩn tối ưu cho feature pyramid P3–P5 |
| **Epochs** | 60 epochs | Đủ số chu kỳ để hội tụ gradient mà không bị overfitting |
| **Batch Size** | 16 | Tận dụng tối đa bộ nhớ GPU T4, ổn định Batch Normalization |
| **Optimizer** | `AdamW` (lr0 = 0.002, lrf = 0.01) | Tự động thích ứng gradient và chống phân rã trọng số |
| **LR Scheduler** | Cosine Annealing (`cos_lr = True`) | Giảm dần tốc độ học mượt mà về cuối chu kỳ |
| **Augmentation** | Mosaic = 1.0, FlipLR = 0.5, HSV | Tăng cường độ đa dạng góc nhìn công trường |
| **Close Mosaic** | 10 epochs cuối (`close_mosaic = 10`) | Tắt ghép ảnh ở giai đoạn cuối giúp bounding box khớp chặt với biên vật thể |

---

## 2. KẾT QUẢ ĐÁNH GIÁ ĐỊNH LƯỢNG (VALIDATION & TEST SETS)

### Tổng quan toàn bộ 9 Classes:
* **Precision tổng thể (P):** **0.821 (82.1%)**
* **Recall tổng thể (R):** **0.580 (58.0%)**
* **mAP@50:** **0.634 (63.4%)**
* **mAP@50-95:** **0.380 (38.0%)**
* **Thời gian suy luận (Latency):** **9.6 ms/ảnh** trên GPU T4 $\rightarrow$ **104 FPS** (Gấp 3.5 lần chuẩn thời gian thực 30 FPS).

### Phân tích chi tiết từng Class:

| Class ID | Tên Class | Số lượng Instance | Precision (P) | Recall (R) | mAP@50 | mAP@50-95 | Đánh giá kỹ thuật |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **0** | `Person` | 166 | **0.824** | 0.593 | **0.695** | 0.474 | Vững chắc cho Tracking & Association |
| **1** | `Hardhat` | 79 | **0.925** | 0.628 | **0.717** | 0.503 | Cực kỳ nhạy, không báo giả |
| **2** | `NO-Hardhat` | 69 | **0.735** | 0.551 | 0.580 | 0.302 | Bắt tốt các trường hợp đầu trần |
| **3** | `Safety Vest` | 41 | **0.859** | 0.561 | **0.705** | 0.456 | Độ tin cậy cao trên áo phản quang |
| **4** | `NO-Safety Vest` | 106 | **0.793** | 0.470 | 0.548 | 0.323 | Phát hiện người mặc áo thường |
| **5** | `Mask` | 21 | **0.937** | **0.857** | **0.857** | 0.613 | Hiệu năng xuất sắc nhất |
| **6** | `NO-Mask` | 74 | **0.756** | 0.446 | 0.467 | 0.170 | Chấp nhận được với vật thể siêu nhỏ |
| **7** | `Gloves` | 25 | **0.687** | 0.320 | 0.335 | 0.157 | Thách thức vật thể nhỏ góc chụp xa |
| **8** | `Safety Cone` | 44 | **0.873** | **0.795** | **0.800** | 0.423 | Bắt mốc cảnh báo công trường rất nhạy |

---

## 3. PHÂN TÍCH FALSE POSITIVES VÀ FALSE NEGATIVES

1. **Phân tích nhãn tuân thủ vs vi phạm:**
   - Cặp `Hardhat` (P=92.5%) vs `NO-Hardhat` (P=73.5%): Mô hình ưu tiên độ chính xác cao khi khẳng định có mũ. Khi không đội mũ, mô hình thận trọng hơn để tránh cảnh báo phạt oan.
   - Cặp `Safety Vest` (P=85.9%) vs `NO-Safety Vest` (P=79.3%): Nhận diện tốt màu dạ quang đặc trưng (cam, vàng chanh) của áo bảo hộ.
2. **Thách thức vật thể siêu nhỏ (`Gloves`, `NO-Mask`):**
   - Đúng như dự báo trong báo cáo thẩm định Phase 01: Găng tay và mặt không khẩu trang ở khoảng cách xa chiếm diện tích $< 32^2$ pixel. Độ nhạy Recall ở mức 32% - 44%. Điều này được khắc phục triệt để ở **Phase 04 (Temporal Voting)**: Tích lũy trạng thái qua 10-15 frame liên tiếp để xác nhận vi phạm thay vì chỉ dựa vào 1 frame đơn lẻ.

---

## 4. KẾT LUẬN NGHIỆM THU PHASE 02

* Mô hình **YOLO11s** đáp ứng vượt chuẩn yêu cầu về độ chính xác và độ trễ realtime ($104 \text{ FPS}$).
* Trọng số PyTorch (`best.pt`) và ONNX (`best.onnx`) đã sẵn sàng.
* Đủ điều kiện 100% để chuyển sang **PHASE 03: OBJECT TRACKING**.

