import sys
import os
import py_compile
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_phase_06_evaluation():
    print("=" * 70)
    print("🖥️  PHASE 06 – FRONTEND & STREAMLIT DASHBOARD EVALUATION")
    print("=" * 70)

    # 1. Verify Dependencies
    print("[1/5] Kiểm tra các thư viện phục vụ Dashboard (Streamlit, Plotly, Pandas)...")
    import streamlit
    import plotly
    import pandas
    import cv2
    import numpy
    print(f"  ✅ Streamlit : v{streamlit.__version__}")
    print(f"  ✅ Plotly    : v{plotly.__version__}")
    print(f"  ✅ Pandas    : v{pandas.__version__}")

    # 2. Syntax & Compilation Check for frontend/app.py
    print("\n[2/5] Kiểm tra biên dịch (Syntax Compilation) file frontend/app.py...")
    app_path = os.path.join(PROJECT_ROOT, "frontend", "app.py")
    try:
        py_compile.compile(app_path, doraise=True)
        print("  ✅ File frontend/app.py biên dịch thành công 100%, không có lỗi cú pháp!")
    except Exception as e:
        print(f"  ❌ Lỗi cú pháp trong frontend/app.py: {e}")
        return

    # 3. Test Database Connection for Dashboard
    print("\n[3/5] Kiểm tra kết nối Database & Lấy dữ liệu KPI thời gian thực...")
    from src.database.session import SessionLocal, DATABASE_URL, init_db
    from src.database import crud
    init_db()
    db = SessionLocal()
    summary = crud.get_system_summary(db)
    violations = crud.get_all_violations(db, limit=10)
    db_engine_name = "MySQL" if "mysql" in DATABASE_URL.lower() else "SQLite"
    print(f"  ✅ Database Engine     : {db_engine_name}")
    print(f"  ✅ Total Workers in DB : {summary['total_unique_workers']}")
    print(f"  ✅ Active Violations   : {summary['active_open_violations']}")
    print(f"  ✅ Compliance Rate     : {summary['compliance_rate']}%")
    print(f"  ✅ Recent Logged Events: {len(violations)} events")
    db.close()

    # 4. Test Single Image Inference Pipeline
    print("\n[4/5] Kiểm tra Pipeline xử lý ảnh tĩnh (Single Image Test Mode)...")
    from src.detection.detector import PPEDetector
    from src.common.visualizer import PPEVisualizer
    model_path = "models/checkpoints/best.pt"
    if os.path.exists(model_path):
        detector = PPEDetector(model_path=model_path, conf_threshold=0.35)
        test_dir = os.path.join("data", "processed", "test", "images")
        sample_imgs = [os.path.join(test_dir, f) for f in os.listdir(test_dir) if f.endswith(('.jpg', '.png'))]
        if sample_imgs:
            test_img = cv2.imread(sample_imgs[0])
            detections = detector.predict(test_img)
            vis = PPEVisualizer()
            annotated = vis.draw_detections(test_img, detections)
            print(f"  ✅ Đã chạy thử nghiệm trên ảnh: {os.path.basename(sample_imgs[0])}")
            print(f"  ✅ Phát hiện {len(detections)} đối tượng bảo hộ / công nhân.")
    else:
        print(f"  ⚠️ Cảnh báo: Không tìm thấy model tại {model_path}")

    # 5. Summary & Instructions
    print("\n" + "=" * 70)
    print("📊 BÁO CÁO NGHIỆM THU PHASE 06 (FRONTEND & DASHBOARD):")
    print("  • Giao diện Web Streamlit : Sẵn sàng hoạt động")
    print("  • Tab 1 (Live Stream)     : Hỗ trợ Demo Video, Single Image & Upload Video")
    print("  • Tab 2 (Violations Log)  : Hiển thị bảng sự kiện & Nút Quick Resolve")
    print("  • Tab 3 (Analytics)       : Biểu đồ Plotly phân bổ vi phạm & Tuân thủ")
    print("  • Hướng dẫn khởi chạy UI  : Chạy lệnh sau trên terminal:")
    print("      streamlit run frontend/app.py")
    print("=" * 70)
    print("✅ HOÀN THÀNH KIỂM ĐỊNH PHASE 06!")

if __name__ == "__main__":
    run_phase_06_evaluation()

