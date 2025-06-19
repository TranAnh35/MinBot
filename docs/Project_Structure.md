# Cấu trúc dự án

```
ChatBot/
├── Dockerfile.backend          # Dockerfile cho backend (Python 3.10)
├── Dockerfile.frontend         # Dockerfile cho frontend (Node.js)
├── docker-compose.yml          # Cấu hình Docker Compose
├── requirements.txt            # Dependencies Python cho backend
├── README.md                   # Tài liệu tổng quan dự án
├── .gitignore                  # Git ignore rules
├── .dockerignore              # Docker ignore rules
│
├── docs/                      # Tài liệu dự án
│   ├── getting-started/
│   │   └── installation.md    # Hướng dẫn cài đặt
│   ├── guides/
│   │   ├── api/
│   │   │   └── API_REFERENCE.md  # Tài liệu API
│   │   └── USER_GUIDE.md      # Hướng dẫn sử dụng
│   └── PROJECT_STRUCTURE.md   # File hiện tại
│
├── assets/                    # Tài nguyên tĩnh (hình ảnh, banner)
│   ├── Gemini_Banner.jpg
│   └── Interface.png
│
└── src/                       # Mã nguồn chính
    ├── run.py                 # Script chạy toàn bộ hệ thống
    │
    ├── backend/               # Backend FastAPI
    │   ├── main.py           # Entry point của backend
    │   ├── .env              # Biến môi trường (API keys, config)
    │   │
    │   ├── api/              # API Routes và endpoints
    │   │   ├── __init__.py
    │   │   ├── api_key/
    │   │   │   ├── __init__.py
    │   │   │   └── routes.py  # Quản lý API key
    │   │   ├── conversation/
    │   │   │   ├── __init__.py
    │   │   │   ├── routes.py  # Quản lý hội thoại
    │   │   │   └── schemas.py # Pydantic schemas
    │   │   ├── file/
    │   │   │   ├── __init__.py
    │   │   │   └── routes.py  # Upload/quản lý file
    │   │   ├── gen/
    │   │   │   ├── __init__.py
    │   │   │   ├── routes.py  # Content generation
    │   │   │   └── schemas.py # Response schemas
    │   │   ├── rag/
    │   │   │   ├── __init__.py
    │   │   │   └── routes.py  # RAG queries
    │   │   ├── system/
    │   │   │   ├── __init__.py
    │   │   │   └── routes.py  # System management
    │   │   └── web/
    │   │       ├── __init__.py
    │   │       └── routes.py  # Web search
    │   │
    │   ├── clients/           # External API clients
    │   │   ├── __init__.py
    │   │   └── (client implementations)
    │   │
    │   ├── config/            # Cấu hình hệ thống
    │   │   ├── __init__.py
    │   │   ├── app_config.py  # Cấu hình chính
    │   │   └── pdf_config.py  # Cấu hình PDF reader
    │   │
    │   ├── models/            # Data models
    │   │   └── __init__.py
    │   │
    │   ├── services/          # Business logic services
    │   │   ├── __init__.py
    │   │   ├── api_manager.py # Quản lý API key
    │   │   ├── app_manager.py # Application lifecycle
    │   │   │
    │   │   ├── conversation/  # Conversation management
    │   │   │   ├── __init__.py
    │   │   │   └── service.py
    │   │   │
    │   │   ├── file/          # File processing
    │   │   │   ├── __init__.py
    │   │   │   ├── async_processor.py # Async file processing
    │   │   │   ├── async_reader.py    # Async file reader
    │   │   │   ├── base_reader.py     # Base file reader
    │   │   │   └── storage.py         # File storage
    │   │   │
    │   │   ├── llm/           # Large Language Model
    │   │   │   ├── __init__.py
    │   │   │   └── generator.py # Content generation
    │   │   │
    │   │   ├── rag/           # Retrieval Augmented Generation
    │   │   │   ├── __init__.py
    │   │   │   └── rag.py     # RAG implementation
    │   │   │
    │   │   ├── vector_db/     # Vector database
    │   │   │   ├── __init__.py
    │   │   │   ├── database_manager.py # Database operations
    │   │   │   ├── text_processor.py   # Text chunking
    │   │   │   └── vector_db_service.py # Vector operations
    │   │   │
    │   │   └── web/           # Web search
    │   │       ├── __init__.py
    │   │       └── service.py # Web search implementation
    │   │
    │   ├── upload/            # Thư mục lưu file upload
    │   │   └── (uploaded files)
    │   │
    │   ├── utils/             # Utilities
    │   │   ├── __init__.py
    │   │   └── rag_file_utils.py
    │   │
    │   ├── vector_store.db    # SQLite database (auto-generated)
    │   ├── rag_service.log    # Log file (auto-generated)
    │   └── (other generated files)
    │
    └── frontend/              # Frontend React/TypeScript
        ├── package.json       # Dependencies và scripts
        ├── package-lock.json  # Lock file
        ├── tsconfig.json      # TypeScript config
        ├── tsconfig.app.json  # App-specific TS config
        ├── tsconfig.node.json # Node-specific TS config
        ├── vite.config.ts     # Vite bundler config
        ├── eslint.config.js   # ESLint configuration
        ├── index.html         # HTML entry point
        ├── .gitignore         # Git ignore for frontend
        ├── README.md          # Frontend documentation
        │
        ├── public/            # Static assets
        │   └── (static files)
        │
        ├── node_modules/      # NPM dependencies
        │
        └── src/               # Frontend source code
            ├── main.tsx       # React entry point
            ├── App.tsx        # Main App component
            ├── index.css      # Global styles
            ├── vite-env.d.ts  # Vite type definitions
            │
            ├── assets/        # Frontend assets
            │   └── (images, icons, etc.)
            │
            ├── components/    # React components
            │   ├── Chat/      # Chat-related components
            │   │   ├── FileDropzone.tsx
            │   │   └── (other chat components)
            │   ├── Layouts/   # Layout components
            │   ├── Settings/  # Settings components
            │   ├── ui/        # Reusable UI components
            │   └── DocumentUploader.tsx
            │
            ├── lib/           # Utility libraries
            │   └── utils.ts
            │
            ├── services/      # API service calls
            │   └── api.ts     # API client
            │
            └── types/         # TypeScript type definitions
                ├── interface.ts
                └── chat.ts
```

## Tổng quan kiến trúc

### Backend (FastAPI)
- **Framework**: FastAPI với Python 3.10+
- **Database**: SQLite cho conversation storage
- **Vector DB**: FAISS cho RAG (Retrieval Augmented Generation)
- **AI Model**: Google Gemini (gemini-2.0-flash-lite)
- **File Processing**: Hỗ trợ TXT, PDF, DOC, DOCX, YAML, YML, MD
- **PDF Reader**: Dual-mode (PyMuPDF fast/Docling accurate)

### Frontend (React + TypeScript)
- **Framework**: React 18 với TypeScript
- **Bundler**: Vite
- **UI Library**: Tailwind CSS
- **State Management**: React hooks
- **HTTP Client**: Axios
- **File Upload**: React Dropzone

### Tính năng chính

1. **Conversation Management**: Lưu trữ và quản lý hội thoại với SQLite
2. **File Processing**: Upload và xử lý đa định dạng file
3. **RAG System**: Tìm kiếm thông tin từ documents
4. **Web Search**: Tích hợp Google Search API
5. **AI Generation**: Sử dụng Google Gemini cho content generation
6. **System Management**: Monitoring, health check, performance metrics

### API Architecture
- **RESTful APIs**: Tổ chức theo module (rag, files, web, conversations, system)
- **Auto Documentation**: Swagger UI tại `/docs`
- **Error Handling**: Standardized error responses
- **Validation**: Pydantic models cho request/response

### Development Features
- **Hot Reload**: Backend với uvicorn, Frontend với Vite
- **Docker Support**: Multi-container với docker-compose
- **Logging**: Structured logging với multiple levels
- **Configuration**: Environment-based config với validation

Cấu trúc này được thiết kế để dễ bảo trì, mở rộng và phát triển, với separation of concerns rõ ràng giữa các layer và modules.