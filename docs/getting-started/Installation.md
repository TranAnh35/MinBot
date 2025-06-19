# Hướng dẫn cài đặt

Tài liệu này hướng dẫn chi tiết cách cài đặt và chạy ChatBot trên môi trường local hoặc sử dụng Docker.

## Yêu cầu hệ thống

### Phương pháp 1: Chạy trực tiếp (không dùng Docker)
- Python 3.10 hoặc cao hơn
- Node.js 18.x hoặc cao hơn
- npm (đi kèm với Node.js)
- pip (trình quản lý gói Python)

### Phương pháp 2: Sử dụng Docker (khuyến nghị)
- Docker Engine 20.10.0 trở lên
- Docker Compose 2.0.0 trở lên

## Phương pháp 1: Cài đặt và chạy trực tiếp

### 1. Cài đặt Backend

1. Sao chép repository:
   ```bash
   git clone https://github.com/TranAnh35/ChatBot.git
   cd ChatBot
   ```

2. Tạo và kích hoạt môi trường ảo (khuyến nghị):
   ```bash
   # Trên Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Trên macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Cài đặt các phụ thuộc Python:
   ```bash
   pip install -r requirements.txt
   ```

4. Cấu hình biến môi trường:
   - Tạo file `.env` trong thư mục `src/backend/` với nội dung:
     ```
     # Required - API Key cho Google Gemini
     GOOGLE_API_KEY=your_google_api_key_here
     
     # Optional - Web Search (nếu muốn sử dụng tìm kiếm web)
     GOOGLE_SEARCH_API_KEY=your_google_search_api_key
     GOOGLE_SEARCH_ID=your_google_search_engine_id
     
     # Optional - Cấu hình server
     HOST=localhost
     PORT=8000
     DEBUG=false
     
     # Optional - Cấu hình PDF reader
     USE_FAST_PDF_READER=true
     
     # Optional - Cấu hình RAG
     RAG_TOP_K=5
     CHUNK_SIZE=2000
     CHUNK_OVERLAP=200
     ```
   - Thay `your_google_api_key_here` bằng API key của bạn từ [Google AI Studio](https://makersuite.google.com/app/apikey)

5. Khởi động backend:
   ```bash
   cd src/backend
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - Backend sẽ chạy tại: http://localhost:8000
   - Tài liệu API (Swagger UI): http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### 2. Cài đặt Frontend

1. Mở terminal mới và chuyển đến thư mục frontend:
   ```bash
   cd src/frontend
   ```

2. Cài đặt các phụ thuộc Node.js:
   ```bash
   npm install
   ```

3. Khởi động máy chủ phát triển:
   ```bash
   npm run dev
   ```
   - Frontend sẽ chạy tại: http://localhost:5173

### 3. Sử dụng script run.py (Khuyến nghị)

Thay vì chạy từng service riêng lẻ, bạn có thể sử dụng script tự động:

```bash
# Từ thư mục gốc ChatBot
python src/run.py
```

Script này sẽ tự động:
- Khởi động backend tại cổng 8000
- Khởi động frontend tại cổng 5173
- Quản lý cả hai process cùng lúc

## Phương pháp 2: Chạy bằng Docker (Khuyến nghị)

1. Đảm bảo Docker và Docker Compose đã được cài đặt

2. Sao chép repository (nếu chưa có):
   ```bash
   git clone https://github.com/TranAnh35/ChatBot.git
   cd ChatBot
   ```

3. Tạo file `.env` trong thư mục `src/backend/` với nội dung:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   GOOGLE_SEARCH_API_KEY=your_google_search_api_key  # Optional
   GOOGLE_SEARCH_ID=your_google_search_engine_id     # Optional
   ```

4. Xây dựng và khởi động các container:
   ```bash
   # Lần đầu tiên hoặc khi có thay đổi về dependencies
   docker compose up --build
   
   # Các lần sau
   docker compose up
   ```

5. Truy cập ứng dụng:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Tài liệu API: http://localhost:8000/docs
   - System Status: http://localhost:8000/system/status

## Kiểm tra cài đặt

1. **Kiểm tra Backend**:
   - Truy cập http://localhost:8000/health
   - Kiểm tra system status tại http://localhost:8000/system/status

2. **Kiểm tra Frontend**:
   - Mở trình duyệt và truy cập http://localhost:5173
   - Nhấp vào biểu tượng cài đặt (⚙️) ở góc trên bên phải
   - Nhập API key của bạn và nhấn "Lưu"

3. **Test tính năng**:
   - Thử gửi một tin nhắn để kiểm tra kết nối với AI
   - Thử tải lên một file PDF hoặc TXT để kiểm tra tính năng RAG
   - Thử tìm kiếm web (nếu đã cấu hình Google Search API)

## Xử lý sự cố

### Lỗi cổng đang sử dụng
Nếu gặp lỗi cổng đang được sử dụng:
- Backend (8000): Thay đổi PORT trong file .env
- Frontend (5173): Sửa cổng trong vite.config.ts hoặc chạy `npm run dev -- --port 3000`

### Lỗi kết nối API
- Kiểm tra kết nối internet
- Đảm bảo API key đã được cấu hình đúng trong file .env
- Kiểm tra nhật ký lỗi của backend để biết thêm chi tiết

### Lỗi tải file/PDF
- Đảm bảo thư mục `upload/` có quyền ghi
- Kiểm tra định dạng file có được hỗ trợ (TXT, PDF, DOC, DOCX, YAML, YML, MD)
- Xem log để biết chi tiết lỗi

### Lỗi database
- Đảm bảo quyền ghi trong thư mục chứa file database SQLite
- Kiểm tra trạng thái database tại `/conversations/database/status`

## Dừng ứng dụng

### Khi chạy trực tiếp
- Nhấn `Ctrl+C` trong cửa sổ terminal đang chạy backend/frontend
- Hoặc `Ctrl+C` trong terminal chạy run.py

### Khi sử dụng Docker
```bash
docker compose down

# Để xóa luôn volumes (bao gồm database)
docker compose down -v
```

## Cấu hình nâng cao

### Biến môi trường chi tiết

Tham khảo `src/backend/config/app_config.py` để xem đầy đủ các biến môi trường có thể cấu hình:

- **Database**: `DATABASE_PATH`, `DATABASE_TIMEOUT`
- **File Processing**: `UPLOAD_DIR`, `CHUNK_SIZE`, `CHUNK_OVERLAP`
- **RAG**: `RAG_TOP_K`, `RAG_BATCH_SIZE`
- **LLM**: `LLM_MODEL`, `LLM_TEMPERATURE`
- **Performance**: `MAX_WORKERS`, `MEMORY_LIMIT_GB`
- **Logging**: `LOG_LEVEL`, `LOG_FILE`

### Cấu hình PDF Reader

Hệ thống hỗ trợ 2 mode đọc PDF:
- **Fast Mode** (PyMuPDF): Nhanh hơn, ít chính xác hơn
- **Accurate Mode** (Docling): Chậm hơn, chính xác hơn

Thiết lập trong `.env`:
```
USE_FAST_PDF_READER=true  # hoặc false
```
