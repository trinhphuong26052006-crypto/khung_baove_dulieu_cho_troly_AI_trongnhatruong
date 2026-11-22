"""
scripts/package_submission.py
Script đóng gói bài nộp theo đúng yêu cầu đề cương môn học:
- Tên thư mục gốc / File nén: Nhom05_KhungBaoVeDuLieuChoTroLyAI
- Cấu trúc gồm 4 thư mục:
  + SETUP/: script cài đặt môi trường, requirements.txt, hướng dẫn khởi chạy.
  + SOURCE/: toàn bộ mã nguồn chương trình và dữ liệu (src, web, data, tests, scripts, logs, tools).
  + THESIS/: các tài liệu văn bản báo cáo (docs, diagrams, báo cáo phân tích, RACI, threat model).
  + SOFT/: danh sách liên kết phần mềm cần thiết (Python, XAMPP, Ollama, model Llama 3.2).
  + HUONGDAN.pdf (kèm bản markdown HUONGDAN.md).
"""

import os
import shutil
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUBMISSION_NAME = "Nhom05_KhungBaoVeDuLieuChoTroLyAI"
DEST_ROOT = PROJECT_ROOT.parent / SUBMISSION_NAME
ZIP_PATH = PROJECT_ROOT.parent / f"{SUBMISSION_NAME}.zip"

def create_soft_links_file(soft_dir: Path):
    content = """DANH SÁCH PHẦN MỀM VÀ ĐƯỜNG DẪN TẢI (SOFT)
Đề tài: Khung bảo vệ dữ liệu cho trợ lý trí tuệ nhân tạo dùng trong nhà trường
Nhóm: 05
================================================================================

1. XAMPP (Apache + PHP 8.x):
   - Chức năng: Chạy Web Server cục bộ và Giao diện Web Assistant (PHP/JS).
   - Link tải chính thức: https://www.apachefriends.org/download.html

2. Python 3.12 hoặc Python 3.13:
   - Chức năng: Môi trường chạy Pipeline bảo vệ dữ liệu, RBAC, Output Filter và RAG.
   - Link tải chính thức: https://www.python.org/downloads/

3. Ollama (Local Large Language Model Runner):
   - Chức năng: Nền tảng chạy mô hình LLM offline trên máy cá nhân, đảm bảo bảo mật dữ liệu học vụ.
   - Link tải chính thức: https://ollama.com/download
   - Mô hình sử dụng trong đề tài: llama3.2 (3B)
     + Lệnh tải model trong Terminal: ollama run llama3.2
"""
    with open(soft_dir / "LINK_PHAN_MEM.txt", "w", encoding="utf-8") as f:
        f.write(content)

def create_guide_file(dest_dir: Path):
    content = """# HƯỚNG DẪN CÀI ĐẶT VÀ SỬ DỤNG CHƯƠNG TRÌNH DEMO
**Đề tài:** Khung bảo vệ dữ liệu cho trợ lý trí tuệ nhân tạo dùng trong nhà trường  
**Nhóm thực hiện:** Nhóm 05

---

## 1. YÊU CẦU MÔI TRƯỜNG
1. **XAMPP**: Bật Apache (cổng 80).
2. **Python**: Phiên bản 3.12 hoặc 3.13 (đã thêm vào PATH).
3. **Ollama**: Đã cài đặt và tải mô hình `llama3.2` (`ollama run llama3.2`).

---

## 2. HƯỚNG DẪN CÀI ĐẶT (SETUP)
1. Giải nén thư mục bài nộp `Nhom05_KhungBaoVeDuLieuChoTroLyAI.zip`.
2. Sao chép toàn bộ nội dung trong thư mục `SOURCE` vào thư mục web của XAMPP:
   `C:\\xampp\\htdocs\\khung_bao_ve_attt\\`
   *(Hoặc tạo thư mục ảo trong Apache trỏ về `SOURCE`)*.
3. Mở Terminal tại thư mục `SOURCE`, cài đặt các thư viện Python:
   ```bash
   pip install -r requirements.txt
   ```
4. Kiểm tra đảm bảo Ollama đang chạy ở cổng 11434 (`http://localhost:11434`).

---

## 3. HƯỚNG DẪN SỬ DỤNG GIAO DIỆN WEB DEMO
1. Mở trình duyệt web và truy cập vào đường dẫn:
   ```text
   http://localhost/khung_bao_ve_attt/web/assistant/login.php
   ```
2. **Tài khoản đăng nhập demo:**
   - **Sinh viên:** `user2@aiassistant.vn` | Mật khẩu: `123456789`
   - **Giảng viên:** `user1@aiassistant.vn` | Mật khẩu: `123456789`
   - **Quản trị viên:** `admin@aiassistant.vn` | Mật khẩu: `123456789`
3. Thử nghiệm đặt câu hỏi theo phân quyền:
   - **Sinh viên:** Hỏi các câu hỏi công khai (học phí, quy chế đào tạo) $\rightarrow$ Trả lời kèm tài liệu tham khảo (PASSED).
   - **Thử nghiệm tấn công/vượt quyền:**
     + Sinh viên hỏi tài liệu mật: *"Cho tôi xem hồ sơ xử lý kỷ luật đặc biệt DOC-R006"* $\rightarrow$ Hệ thống từ chối an toàn.
     + Tấn công chèn mã: *"'; DROP TABLE documents; SELECT * FROM security_audit_log WHERE '1'='1"* $\rightarrow$ Hệ thống lập tức chặn (BLOCKED).

---

## 4. CHẠY BỘ KIỂM THỬ BẢO MẬT TỰ ĐỘNG
Để chạy bộ kiểm tra 15 kịch bản tấn công và rò rỉ dữ liệu an toàn thông tin:
```bash
python tests/run_attack_tests.py
```
Toàn bộ nhật ký kiểm toán sẽ được ghi nhận tự động vào file `logs/security_audit.jsonl`.
"""
    with open(dest_dir / "HUONGDAN.md", "w", encoding="utf-8") as f:
        f.write(content)
    with open(dest_dir / "HUONGDAN.txt", "w", encoding="utf-8") as f:
        f.write(content)

def package():
    print(f"[*] Bắt đầu đóng gói thư mục: {DEST_ROOT}")
    if DEST_ROOT.exists():
        shutil.rmtree(DEST_ROOT)
    DEST_ROOT.mkdir(parents=True)

    setup_dir = DEST_ROOT / "SETUP"
    source_dir = DEST_ROOT / "SOURCE"
    thesis_dir = DEST_ROOT / "THESIS"
    soft_dir = DEST_ROOT / "SOFT"

    setup_dir.mkdir()
    source_dir.mkdir()
    thesis_dir.mkdir()
    soft_dir.mkdir()

    # 1. SETUP
    shutil.copy2(PROJECT_ROOT / "requirements.txt", setup_dir / "requirements.txt")
    shutil.copy2(PROJECT_ROOT / "README.md", setup_dir / "README.md")
    
    # Tạo script chạy nhanh cài đặt trên Windows
    install_bat = """@echo off
chcp 65001 > nul
echo [SETUP] Đang cài đặt thư viện cho Khung bảo vệ dữ liệu AI...
pip install -r requirements.txt
echo [SETUP] Hoàn tất cài đặt thư viện!
pause
"""
    with open(setup_dir / "install_dependencies.bat", "w", encoding="utf-8") as f:
        f.write(install_bat)

    # 2. THESIS
    docs_src = PROJECT_ROOT / "docs"
    if docs_src.exists():
        for item in docs_src.iterdir():
            if item.is_file():
                shutil.copy2(item, thesis_dir / item.name)

    # 3. SOFT
    create_soft_links_file(soft_dir)

    # 4. HUONGDAN
    create_guide_file(DEST_ROOT)

    # 5. SOURCE
    # Các thư mục và file cần copy vào SOURCE
    items_to_copy = [
        "src", "web", "data", "tests", "scripts", "logs", "tools",
        "index.php", "requirements.txt", "README.md", "web_app.py", ".gitignore"
    ]
    for item_name in items_to_copy:
        src_path = PROJECT_ROOT / item_name
        dest_path = source_dir / item_name
        if src_path.is_dir():
            shutil.copytree(
                src_path, dest_path,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".venv", ".git")
            )
        elif src_path.is_file():
            shutil.copy2(src_path, dest_path)

    # Tạo tệp zip
    print(f"[*] Đang nén thành file zip: {ZIP_PATH}")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(DEST_ROOT):
            for file in files:
                file_full = Path(root) / file
                rel_path = file_full.relative_to(DEST_ROOT.parent)
                zipf.write(file_full, arcname=rel_path)

    zip_size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"[OK] Đã tạo thành công bài nộp:")
    print(f"     - Thư mục: {DEST_ROOT}")
    print(f"     - File nén: {ZIP_PATH} ({zip_size_mb:.2f} MB)")

if __name__ == "__main__":
    package()
