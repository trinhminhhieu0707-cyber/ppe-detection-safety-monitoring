# 🎯 PPE DETECTION SYSTEM: TECHNICAL INTERVIEW CHEATSHEET & DEFENSE GUIDE
**Target Roles:** AI Engineer / Computer Vision Engineer Intern  
**Project:** PPE Detection & Safety Monitoring System  

---

## 1. DATASET CURATION & DATA AUDITING (PHASE 01)

### Q: "Tại sao bạn không dùng trực tiếp 25 classes gốc của Roboflow Version 30 mà lại lọc về 9 classes?"
**Trả lời mẫu:**
> *"Khi kiểm định dữ liệu ban đầu (Data Profiling), tôi phát hiện ra 2 vấn đề kỹ thuật nghiêm trọng trong dataset v30:*  
> *1. **Rủi ro Zero-shot Evaluation:** Có 4 classes phương tiện (`SUV`, `bus`, `fire hydrant`, `semi`) chỉ có mẫu trong tập Train nhưng **0 mẫu trong tập Validation và Test**. Nếu giữ nguyên, mAP của các class này trên Test sẽ bằng 0 hoặc Undefined, làm sai lệch kết quả đánh giá mô hình.*  
> *2. **Mất cân bằng dữ liệu cực đoan:** Class `bus` chỉ có 1 bounding box duy nhất trên toàn bộ 717 ảnh, trong khi `Person` có hơn 1,100 box (chênh lệch > 1,000 lần).*  
> *Vì vậy, tôi đã tinh giản và chuẩn hóa về **9 classes trọng tâm PPE**, vừa giải quyết triệt để lỗi thiếu mẫu, vừa giữ lại 166 ảnh nền (negative samples) để giúp mô hình triệt tiêu False Alarm ngoài công trường."*

---

## 2. COMPUTER VISION & MODEL BENCHMARKING (PHASE 02)

### Q: "Tại sao bạn chọn YOLO11s thay vì YOLO11n hay các kiến trúc khác?"
**Trả lời mẫu:**
> *"Qua phân tích kích thước Bounding Box theo chuẩn COCO ở Phase 01, tôi nhận thấy hơn **50% Hardhat, 64% Gloves và 70% NO-Mask là Small Objects** ($Area < 32^2$).*  
> *Mặc dù YOLO11n có tốc độ cực nhanh, nhưng dung lượng biểu diễn đặc trưng (feature capacity) của bản Nano cho các vật thể nhỏ dễ bị hạn chế. **YOLO11s (9.4M tham số)** mang lại sự cân bằng lý tưởng: vừa đạt **Precision 82.1%** trên tập Test, vừa duy trì độ trễ suy luận chỉ **9.6 ms trên GPU T4 (~104 FPS)**, vượt xa yêu cầu thời gian thực 30 FPS của hệ thống camera giám sát."*

---

## 3. OBJECT TRACKING (PHASE 03)

### Q: "Tại sao dùng ByteTrack thay vì DeepSORT?"
**Trả lời mẫu:**
> *"1. **Tối ưu hóa độ trễ:** DeepSORT yêu cầu chạy thêm một mạng trích xuất đặc trưng ReID (Appearance Feature Extractor) cho mỗi Bounding Box, gây nghẽn cổ chai FPS khi công trường có nhiều công nhân.*  
> *2. **Cơ chế 2-stage Matching của ByteTrack:** ByteTrack tận dụng cả các detection có score thấp (low-confidence boxes) thông qua Bộ lọc Kalman (Kalman Filter) để liên kết vết đối tượng khi công nhân bị che khuất một phần (partial occlusion) hoặc bị mờ do chuyển động.*  
> *3. **Kiến trúc Dual-Stream:** Chúng tôi chỉ track duy nhất class `Person` để duy trì Track ID ổn định, tách biệt hoàn toàn với các nhãn PPE tĩnh để tránh làm Kalman Filter bị phân mảnh."*

---

## 4. COMPLIANCE ENGINE & SPATIAL ASSOCIATION (PHASE 04)

### Q: "Làm thế nào để bạn biết chính xác Mũ bảo hộ hoặc Áo phản quang thuộc về người lao động nào?"
**Trả lời mẫu:**
> *"Tôi không sử dụng khoảng cách Euclidean giữa tâm 2 box vì rất dễ gán nhầm khi hai công nhân đứng cạnh nhau.*  
> *Thay vào đó, tôi thiết kế thuật toán **Anatomical Body-Part Spatial Association**:*  
> *- Phân chia Bounding Box của công nhân thành các tỷ lệ giải phẫu: Vùng đầu (0%–30% chiều cao), Vùng thân/ngực (20%–75%), Vùng tay (45%–90%).*  
> *- Tính toán **Tỷ lệ Chứa đựng (Containment Ratio)**: $\frac{\text{Area}(B_{item} \cap B_{body\_part})}{\text{Area}(B_{item})} \ge 0.40$.*  
> *Nhờ đó, một chiếc mũ chỉ có thể được gán cho người nếu nó thực sự nằm trên vùng đầu của người đó."*

### Q: "Làm thế nào để hệ thống không báo động giả khi công nhân cúi đầu hoặc camera bị nháy 1 khung hình?"
**Trả lời mẫu:**
> *"Tôi áp dụng cơ chế **Temporal Voting & Hysteresis** qua cửa sổ trượt 15 frames (~0.5s):*  
> *Một sự kiện vi phạm chỉ được xác nhận chính thức khi tỷ lệ frame vi phạm vượt quá $50\%$ trong cửa sổ trượt và duy trì liên tiếp ít nhất 3 frames. Điều này triệt tiêu hoàn toàn hiện tượng rung nháy (flickering) và báo động oan trong môi trường công trường thực tế."*

---

## 5. BACKEND REST API & RELATIONAL DATABASE (PHASE 05)

### Q: "Tại sao bạn tách riêng Backend (FastAPI + SQLAlchemy) thay vì viết toàn bộ truy vấn trong Streamlit?"
**Trả lời mẫu:**
> *"Tách biệt Backend theo mô hình Client-Server mang lại 3 ưu thế doanh nghiệp:*  
> *1. **Decoupling & Scalability:** Phục vụ đa nền tảng client (Streamlit Dashboard, Mobile App cho kỹ sư an toàn, Webhook báo cáo về hệ thống ERP/BIM trung tâm).*  
> *2. **Chuẩn hóa API & Validation:** Sử dụng Pydantic V2 để tự động xác thực kiểu dữ liệu, bảo đảm tính toàn vẹn và tạo tài liệu Swagger UI chuẩn OpenAPI 3.0.*  
> *3. **Linh hoạt Database:** Nhờ SQLAlchemy ORM, hệ thống dễ dàng chuyển đổi liền mạch giữa SQLite (local development / testing) và MySQL 8.0 (production) chỉ bằng một chuỗi `DATABASE_URL` trong file `.env`."*

---

## 6. FRONTEND MONITORING DASHBOARD (PHASE 06)

### Q: "Hệ thống hiển thị trực quan dữ liệu như thế nào để phục vụ cán bộ an toàn công trường?"
**Trả lời mẫu:**
> *"Chúng tôi xây dựng Dashboard Streamlit hướng đến trải nghiệm người dùng thực tế:*  
> *- **HUD Overlay thời gian thực:** Hiển thị trực tiếp FPS, số lượng công nhân đang có mặt, và danh sách vi phạm đang diễn ra.*  
> *- **Sự kiện vi phạm có bằng chứng:** Lưu mã sự kiện `event_id`, mã công nhân `Worker #ID`, thời gian timestamp và cung cấp nút **Quick Resolve** để cán bộ giám sát đổi trạng thái sang `RESOLVED` trực tiếp vào MySQL.*  
> *- **Phân tích số liệu (Plotly Analytics):** Trực quan hóa phân bổ loại vi phạm (Mũ, Áo, Khẩu trang) và tỷ lệ tuân thủ toàn công trường."*

---

## 7. DEPLOYMENT & INFERENCE BENCHMARKING (PHASE 07)

### Q: "Bạn tối ưu hóa mô hình khi triển khai (Deployment) như thế nào?"
**Trả lời mẫu:**
> *"Bên cạnh trọng số gốc PyTorch, tôi đã xuất khẩu mô hình sang định dạng **ONNX (Open Neural Network Exchange)** và đo lường benchmark thực tế:*  
> *- Trên môi trường CPU máy chủ biên (Edge Server), **ONNX Runtime đạt 95.8 ms (~10.4 FPS)**, nhanh hơn **20.8%** so với PyTorch (121.0 ms ~ 8.3 FPS).*  
> *- Độ trễ phân vị P95 của ONNX Runtime ổn định hơn (101.5 ms so với 134.8 ms).*  
> *- Toàn bộ hệ thống được đóng gói bằng **Docker & Docker Compose** (chia tách service `backend`, `frontend`, kết nối qua mạng `bridge` nội bộ và volume mount đảm bảo dữ liệu không bị mất mát)."*
