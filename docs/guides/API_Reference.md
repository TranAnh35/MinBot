# API Reference

API này cung cấp các endpoints để tương tác với ChatBot system. Base URL: `http://localhost:8000`

## API Key Management

### Get API Key
```http
GET /api-key/get_api_key
```

**Response:**
```json
{
  "api_key": "your_api_key_here"
}
```

### Set API Key  
```http
POST /api-key/set_api_key
```

**Request Body:**
```json
{
  "api_key": "your_new_api_key_here"
}
```

### Validate API Key
```http
POST /api-key/validate_api_key
```

**Request Body:**
```json
{
  "api_key": "api_key_to_validate"
}
```

**Response:**
```json
{
  "valid": true
}
```

## RAG (Retrieval-Augmented Generation)

### Query Documents
```http
GET /rag/query?question={question}
```

**Parameters:**
| Parameter | Type | Description |
| :-------- | :--- | :---------- |
| `question` | `string` | **Required**. Câu hỏi cần truy vấn từ tài liệu |

**Response:**
```json
{
  "response": "Câu trả lời dựa trên nội dung tài liệu"
}
```

### Sync Files to RAG
```http
POST /rag/sync-files
```

Đồng bộ tất cả files trong thư mục upload vào hệ thống RAG.

## File Management

### Upload File
```http
POST /files/upload
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data với file

**Supported formats:** TXT, PDF, DOC, DOCX, YAML, YML, MD

**Response:**
```json
{
  "message": "Tải file lên thành công và đã được xử lý",
  "file_path": "upload/filename.pdf"
}
```

### List Files
```http
GET /files/files
```

**Response:**
```json
{
  "files": [
    {
      "name": "document.pdf",
      "size": 1024000,
      "path": "upload/document.pdf"
    }
  ]
}
```

### Delete File
```http
DELETE /files/delete/{file_name}
```

**Parameters:**
| Parameter | Type | Description |
| :-------- | :--- | :---------- |
| `file_name` | `string` | **Required**. Tên file cần xóa (URL encoded) |

### Read File Content
```http
POST /files/read
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data với file

**Response:**
```json
{
  "file_name": "document.pdf",
  "content": "Nội dung file đã được trích xuất"
}
```

### Configure PDF Reader
```http
POST /files/pdf-config
```

**Request Body:**
```json
{
  "use_fast_reader": true
}
```

**Response:**
```json
{
  "message": "Đã chuyển sang mode: PyMuPDF (Fast)",
  "current_mode": "PyMuPDF (Fast)"
}
```

## Web Search

### Search Web
```http
GET /web/search?query={query}
```

**Parameters:**
| Parameter | Type | Description |
| :-------- | :--- | :---------- |
| `query` | `string` | **Required**. Từ khóa tìm kiếm |

**Response:**
```json
{
  "results": [
    {
      "title": "Result Title",
      "url": "https://example.com",
      "snippet": "Description of the result"
    }
  ],
  "total_results": 10,
  "status": "success"
}
```

### Get Page Content
```http
POST /web/page-content
```

**Request Body:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "title": "Page Title",
  "content": "Main content of the page"
}
```

## Content Generation

### Generate Content
```http
GET /generate/gen_content
```

**Parameters:**
| Parameter | Type | Description |
| :-------- | :--- | :---------- |
| `prompt` | `string` | **Required**. Prompt để tạo nội dung |
| `conversation_id` | `string` | Optional. ID cuộc hội thoại |
| `rag_response` | `string` | Optional. Phản hồi từ hệ thống RAG |
| `web_response` | `string` | Optional. Phản hồi từ tìm kiếm web |
| `file_response` | `string` | Optional. Phản hồi từ file |

**Response:**
```json
{
  "content": "Nội dung được tạo bởi AI"
}
```

### Merge Context
```http
POST /generate/merge_context
```

**Request Body:**
```json
{
  "web_results": {
    "results": [],
    "query_info": "",
    "total_results": 0,
    "status": "success"
  }
}
```

## Conversation Management

### Create Conversation
```http
POST /conversations/create
```

**Request Body:**
```json
{
  "user_id": "user123"
}
```

**Response:**
```json
{
  "conversation_id": "conv_abc123"
}
```

### Add Message
```http
POST /conversations/message
```

**Request Body:**
```json
{
  "conversation_id": "conv_abc123",
  "role": "user",
  "content": "Hello, how are you?"
}
```

### Rename Conversation
```http
POST /conversations/rename
```

**Request Body:**
```json
{
  "conversation_id": "conv_abc123",
  "title": "New conversation title"
}
```

### Get Conversation
```http
GET /conversations/{conversation_id}
```

**Response:**
```json
{
  "id": "conv_abc123",
  "user_id": "user123",
  "title": "Conversation Title",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Get Conversation History
```http
GET /conversations/{conversation_id}/history?limit={limit}
```

**Parameters:**
| Parameter | Type | Description |
| :-------- | :--- | :---------- |
| `conversation_id` | `string` | **Required**. ID cuộc hội thoại |
| `limit` | `integer` | **Required**. Số lượng tin nhắn cần lấy |

### List User Conversations
```http
GET /conversations/user/{user_id}
```

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv_abc123",
      "title": "Conversation Title",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### Delete Conversation
```http
DELETE /conversations/{conversation_id}
```

### Get User Stats
```http
GET /conversations/user/{user_id}/stats
```

**Response:**
```json
{
  "stats": {
    "total_conversations": 5,
    "total_messages": 150,
    "last_activity": "2024-01-01T00:00:00"
  }
}
```

### Database Status
```http
GET /conversations/database/status
```

**Response:**
```json
{
  "status": "connected",
  "message": "Database hoạt động bình thường",
  "database_type": "SQLite",
  "test_query_success": true
}
```

## System Management

### System Status
```http
GET /system/status
```

**Response:**
```json
{
  "status": "success",
  "system": {
    "version": "1.0.0",
    "uptime": "2h 30m",
    "services": ["rag", "web_search", "llm"]
  },
  "health": {
    "status": "healthy",
    "database": "connected",
    "version": "1.0.0"
  }
}
```

### System Configuration
```http
GET /system/config
```

**Response:**
```json
{
  "config": {
    "GOOGLE_API_KEY": "***HIDDEN***",
    "LLM_MODEL": "gemini-2.0-flash-lite",
    "CHUNK_SIZE": 2000,
    "RAG_TOP_K": 5
  },
  "validation": {
    "valid": true,
    "errors": []
  }
}
```

### Restart System
```http
POST /system/restart
```

**Response:**
```json
{
  "message": "Hệ thống đã được khởi động lại thành công"
}
```

### Validate Configuration
```http
POST /system/validate-config
```

**Response:**
```json
{
  "validation": {
    "valid": true,
    "errors": []
  },
  "config_summary": {
    "database_path": "vector_store.db",
    "upload_dir": "upload",
    "api_key_configured": true,
    "search_configured": false
  }
}
```

### Performance Metrics
```http
GET /system/performance
```

**Response:**
```json
{
  "system": {
    "cpu_percent": 25.5,
    "memory_total_gb": 16.0,
    "memory_used_gb": 8.2,
    "memory_percent": 51.25,
    "disk_total_gb": 500.0,
    "disk_used_gb": 250.0,
    "disk_percent": 50.0
  },
  "application": {
    "memory_rss_mb": 150.5,
    "memory_vms_mb": 300.2,
    "pid": 12345,
    "services_count": 6
  }
}
```

## Health Check

### Basic Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### Root Endpoint
```http
GET /
```

**Response:**
```json
{
  "message": "Welcome to Agent System",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "system_info": "/system/status",
    "config": "/system/config",
    "docs": "/docs"
  }
}
```

## Error Responses

Tất cả endpoints có thể trả về các mã lỗi sau:

- **400 Bad Request**: Dữ liệu đầu vào không hợp lệ
- **404 Not Found**: Tài nguyên không tìm thấy
- **500 Internal Server Error**: Lỗi server nội bộ

**Error Response Format:**
```json
{
  "detail": "Chi tiết thông báo lỗi"
}
```