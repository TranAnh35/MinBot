# 📘 Hướng dẫn sử dụng ChatBot

![ChatBot Banner](../../assets/Gemini_Banner.jpg)

## Mục lục
- [Giới thiệu](#-giới-thiệu)
- [Bắt đầu nhanh](#-bắt-đầu-nhanh)
- [Giao diện người dùng](#-giao-diện-người-dùng)
- [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)
  - [Trò chuyện với AI](#-trò-chuyện-với-ai)
  - [Quản lý tài liệu](#-quản-lý-tài-liệu)
  - [Truy vấn tài liệu (RAG)](#-truy-vấn-tài-liệu-rag)
  - [Tìm kiếm web](#-tìm-kiếm-web)
  - [Quản lý hội thoại](#-quản-lý-hội-thoại)
- [Tính năng nâng cao](#-tính-năng-nâng-cao)
- [Mẹo và thủ thuật](#-mẹo-và-thủ-thuật)
- [Xử lý sự cố](#-xử-lý-sự-cố)
- [Câu hỏi thường gặp](#-câu-hỏi-thường-gặp-faq)

## 🌟 Giới thiệu

Chào mừng bạn đến với ChatBot - ứng dụng chat thông minh tích hợp AI mạnh mẽ. Với ChatBot, bạn có thể:

- 💬 Trò chuyện thông minh với AI sử dụng Google Gemini (model mặc định: gemini-2.0-flash-lite)
- 📂 Tải lên và quản lý nhiều loại tài liệu khác nhau (TXT, PDF, DOC, DOCX, YAML, YML, MD)
- 🔍 Truy vấn thông tin từ tài liệu đã tải lên (RAG - Retrieval Augmented Generation)
- 🌐 Tìm kiếm thông tin mới nhất từ internet (nếu cấu hình Google Search API)
- 💾 Lưu trữ và quản lý lịch sử hội thoại với database SQLite
- ⚙️ Cấu hình PDF reader mode (nhanh hoặc chính xác)

## 🚀 Bắt đầu nhanh

### 1. Cấu hình API Key

1. Lấy API key từ [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Mở ChatBot và nhấp vào biểu tượng ⚙️ (cài đặt)
3. Dán API key vào trường tương ứng
4. Nhấn **Lưu** để áp dụng

### 2. Kiểm tra hệ thống

1. Truy cập http://localhost:8000/health để kiểm tra backend
2. Kiểm tra system status tại http://localhost:8000/system/status
3. Xem tài liệu API chi tiết tại http://localhost:8000/docs

### 3. Gửi tin nhắn đầu tiên

1. Nhập câu hỏi hoặc thông điệp vào khung chat
2. Nhấn Enter hoặc nút gửi
3. Chờ AI phản hồi

## 🖥️ Giao diện người dùng

![Giao diện ChatBot](../../assets/Interface.png)

1. **Thanh điều hướng**: Chứa logo và các nút chức năng chính
2. **Danh sách cuộc trò chuyện**: Hiển thị các cuộc hội thoại gần đây (lưu trữ trong SQLite)
3. **Khung chat**: Hiển thị nội dung cuộc trò chuyện
4. **Thanh công cụ**: Chứa các nút đính kèm file, tìm kiếm web
5. **Khung nhập liệu**: Nơi bạn nhập tin nhắn
6. **Settings Panel**: Cấu hình API key và các tùy chọn khác

## 📝 Hướng dẫn sử dụng

### 💬 Trò chuyện với AI

1. **Gửi tin nhắn thông thường**:
   - Nhập nội dung vào khung chat
   - Nhấn Enter hoặc nút gửi
   - AI sẽ sử dụng model Google Gemini để trả lời

2. **Định dạng tin nhắn**:
   - AI hỗ trợ Markdown để định dạng văn bản
   - Có thể hiển thị code blocks, lists, links, etc.

3. **Dừng phản hồi**:
   - Nhấn nút **Dừng** (■) khi AI đang trả lời

### 📂 Quản lý tài liệu

#### Tải lên tài liệu
1. Nhấp vào nút **Tải lên** hoặc **File Upload** trên thanh điều hướng
2. Kéo thả file hoặc nhấp để chọn file từ máy tính
3. **Định dạng được hỗ trợ**: TXT, PDF, DOC, DOCX, YAML, YML, MD
4. File sẽ được xử lý tự động và tích hợp vào hệ thống RAG

#### Cấu hình PDF Reader
1. Truy cập Settings hoặc gọi API `/files/pdf-config`
2. Chọn mode:
   - **Fast Mode (PyMuPDF)**: Nhanh hơn, ít chính xác hơn
   - **Accurate Mode (Docling)**: Chậm hơn, chính xác hơn
3. Thay đổi sẽ áp dụng cho các file PDF mới

#### Xem danh sách tài liệu
1. Gọi API `/files/files` để xem danh sách file đã upload
2. Xem thông tin: tên file, kích thước, đường dẫn

#### Xóa tài liệu
1. Sử dụng API `/files/delete/{file_name}` 
2. File sẽ bị xóa khỏi cả filesystem và database

### 🔍 Truy vấn tài liệu (RAG)

1. **Tải lên ít nhất một tài liệu** trước khi sử dụng tính năng này
2. **Đặt câu hỏi liên quan** đến nội dung tài liệu
3. **Hệ thống sẽ tự động**:
   - Tìm kiếm thông tin từ các tài liệu đã tải lên
   - Kết hợp với AI để đưa ra câu trả lời chính xác
   - Trích dẫn nguồn từ tài liệu gốc

**Cách hoạt động**:
- Documents được chia thành chunks (mặc định 2000 characters với overlap 200)
- Sử dụng FAISS vector database để tìm kiếm semantic
- Top K results (mặc định 5) được sử dụng làm context

### 🌐 Tìm kiếm web

1. **Cấu hình Google Search API** (optional):
   - Lấy API key từ Google Cloud Console
   - Thiết lập Custom Search Engine ID
   - Cấu hình trong file `.env`

2. **Sử dụng tìm kiếm web**:
   - Gọi API `/web/search?query={query}`
   - Hoặc sử dụng tính năng trong giao diện web
   - AI sẽ tìm kiếm thông tin mới nhất từ internet

3. **Lấy nội dung trang**:
   - Sử dụng `/web/page-content` để trích xuất nội dung từ URL cụ thể

### 💾 Quản lý hội thoại

1. **Tạo hội thoại mới**:
   ```http
   POST /conversations/create
   ```

2. **Lưu tin nhắn**:
   - Mỗi tin nhắn được lưu với role (user/assistant) và nội dung
   - Hỗ trợ timestamps và metadata

3. **Đổi tên hội thoại**:
   ```http
   POST /conversations/rename
   ```

4. **Xem lịch sử**:
   - Lấy lịch sử tin nhắn với giới hạn số lượng
   - Hỗ trợ pagination

5. **Thống kê**:
   - Xem tổng số hội thoại, tin nhắn
   - Thời gian hoạt động cuối

## 🔧 Tính năng nâng cao

### System Management
- **Health Check**: `/health` - Kiểm tra trạng thái hệ thống
- **System Status**: `/system/status` - Thông tin chi tiết về services
- **Configuration**: `/system/config` - Xem cấu hình hiện tại
- **Performance Metrics**: `/system/performance` - CPU, memory, disk usage
- **Restart System**: `/system/restart` - Khởi động lại services

### Database Management
- **Database Status**: `/conversations/database/status`
- **Migration Tools**: Chuyển đổi từ JSON sang SQLite
- **Backup & Restore**: Sao lưu và phục hồi dữ liệu

### Configuration Management
- **Environment Variables**: Cấu hình qua file `.env`
- **Runtime Configuration**: Thay đổi cấu hình không cần restart
- **Validation**: Kiểm tra tính hợp lệ của cấu hình

## 💡 Mẹo và thủ thuật

### Tối ưu hóa hiệu suất
- **Chunk Size**: Điều chỉnh `CHUNK_SIZE` (mặc định 2000) cho phù hợp với documents
- **RAG Top K**: Thay đổi `RAG_TOP_K` để cân bằng giữa chính xác và tốc độ
- **PDF Reader**: Chọn mode phù hợp với nhu cầu (fast vs accurate)

### Quản lý tài liệu hiệu quả
- **Đặt tên file rõ ràng** để dễ quản lý
- **Tổ chức theo chủ đề** khi có nhiều documents
- **Kiểm tra định dạng** trước khi upload

### Tìm kiếm tối ưu
- **Sử dụng từ khóa cụ thể** cho câu hỏi RAG
- **Kết hợp tìm kiếm web và RAG** để có thông tin toàn diện
- **Đặt câu hỏi rõ ràng, mạch lạc**

### Phím tắt và shortcuts
- `Enter`: Gửi tin nhắn
- `Ctrl + Enter`: Xuống dòng mới
- Drag & Drop files trực tiếp vào chat

## 🛠️ Xử lý sự cố

### Lỗi kết nối
- **Kiểm tra backend**: Truy cập http://localhost:8000/health
- **Kiểm tra network**: Đảm bảo cổng 8000 và 5173 mở
- **Xem logs**: Kiểm tra file `rag_service.log`

### Lỗi API Key
- **Kiểm tra API key**: Sử dụng `/api-key/validate_api_key`
- **Refresh key**: Lấy API key mới từ Google AI Studio
- **Kiểm tra permissions**: Đảm bảo API key có quyền truy cập Gemini

### Lỗi tải file
- **Định dạng không hỗ trợ**: Kiểm tra extension file
- **Kích thước quá lớn**: Giới hạn thường là 10MB
- **Lỗi đọc PDF**: Thử chuyển đổi PDF reader mode
- **Quyền truy cập**: Kiểm tra quyền ghi thư mục `upload/`

### Lỗi database
- **Database locked**: Kiểm tra các tiến trình đang sử dụng database
- **Corruption**: Sử dụng SQLite tools để repair
- **Migration**: Chạy migration scripts nếu cần

### Performance issues
- **High CPU**: Kiểm tra `/system/performance`
- **Memory leaks**: Monitor memory usage
- **Slow responses**: Điều chỉnh chunk size và top K

## ❓ Câu hỏi thường gặp (FAQ)

### Q: Tôi có thể sử dụng ChatBot miễn phí không?
A: Có, ChatBot là mã nguồn mở và miễn phí, nhưng bạn cần API key của riêng mình từ Google AI (có quota miễn phí).

### Q: Tôi có thể sử dụng ChatBot ngoại tuyến không?
A: Không hoàn toàn. Cần internet để truy cập Google Gemini API, nhưng RAG từ documents local có thể hoạt động offline.

### Q: Làm thế nào để backup dữ liệu?
A: Copy file `vector_store.db` và thư mục `upload/`. Có thể sử dụng API để export conversations.

### Q: Có giới hạn số lượng file upload không?
A: Không có giới hạn cố định, nhưng phụ thuộc vào dung lượng disk và memory của hệ thống.

### Q: Tôi có thể thay đổi AI model không?
A: Có, thay đổi `LLM_MODEL` trong file `.env` (mặc định: gemini-2.0-flash-lite).

### Q: ChatBot có hỗ trợ multiple users không?
A: Có, conversations được tổ chức theo `user_id`. Có thể mở rộng để hỗ trợ authentication.

### Q: Làm thế nào để monitor hệ thống?
A: Sử dụng endpoints `/health`, `/system/status`, `/system/performance` để monitoring.

### Q: Có thể integrate với hệ thống khác không?
A: Có, ChatBot cung cấp REST APIs đầy đủ, có thể integrate dễ dàng.

### Q: Làm thế nào để báo cáo lỗi hoặc góp ý?
A: Bạn có thể liên hệ trực tiếp qua email: tranleanh352004@gmail.com để báo cáo lỗi hoặc góp ý.

---

📌 **Lưu ý**: 
- Tài liệu này được cập nhật thường xuyên theo phiên bản mới nhất
- Xem thêm tài liệu API chi tiết tại `/docs` khi chạy backend
- Tham khảo cấu trúc dự án trong `PROJECT_STRUCTURE.md`
- Đây là dự án cá nhân và hiện tại không nhận contributions từ bên ngoài

Chúc bạn có những trải nghiệm tuyệt vời với ChatBot! 🚀