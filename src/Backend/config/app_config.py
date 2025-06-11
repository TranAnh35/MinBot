"""
Central Application Configuration

File này tập trung tất cả cấu hình của ứng dụng để dễ kiểm soát.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class AppConfig:
    """Cấu hình trung tâm cho toàn bộ ứng dụng."""
    
    # ==================== DATABASE CONFIG ====================
    DATABASE_PATH = os.getenv("DATABASE_PATH", "vector_store.db")
    DATABASE_TIMEOUT = int(os.getenv("DATABASE_TIMEOUT", "30"))
    
    # ==================== FILE PROCESSING CONFIG ====================
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "upload")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml', '.md'}
    
    # ==================== RAG CONFIG ====================
    FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_index.bin")
    CHUNK_MAPPING_PATH = os.getenv("CHUNK_MAPPING_PATH", "chunk_mapping.npz")
    
    # RAG parameters
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
    RAG_BATCH_SIZE = int(os.getenv("RAG_BATCH_SIZE", "50"))
    
    # ==================== LLM CONFIG ====================
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-lite")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # ==================== WEB SEARCH CONFIG ====================
    GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_ID = os.getenv("GOOGLE_SEARCH_ID")
    WEB_SEARCH_RESULTS = int(os.getenv("WEB_SEARCH_RESULTS", "4"))
    
    # ==================== PDF CONFIG ====================
    USE_FAST_PDF_READER = os.getenv("USE_FAST_PDF_READER", "true").lower() == "true"
    DOCLING_TIMEOUT = int(os.getenv("DOCLING_TIMEOUT", "30000"))
    
    # ==================== SERVER CONFIG ====================
    HOST = os.getenv("HOST", "localhost")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    
    # ==================== LOGGING CONFIG ====================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "rag_service.log")
    
    # ==================== PERFORMANCE CONFIG ====================
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
    MEMORY_LIMIT_GB = float(os.getenv("MEMORY_LIMIT_GB", "8.0"))
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """Lấy tất cả cấu hình hiện tại."""
        config = {}
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                config[attr_name] = getattr(cls, attr_name)
        return config
    
    @classmethod
    def validate_config(cls) -> Dict[str, str]:
        """Kiểm tra tính hợp lệ của cấu hình."""
        errors = []
        
        # Kiểm tra API keys
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is required")
        
        # Kiểm tra thư mục
        if not os.path.exists(cls.UPLOAD_DIR):
            try:
                os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create upload directory: {e}")
        
        # Kiểm tra giá trị số
        if cls.CHUNK_SIZE <= 0:
            errors.append("CHUNK_SIZE must be positive")
        
        if cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            errors.append("CHUNK_OVERLAP must be less than CHUNK_SIZE")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Lấy cấu hình database."""
        return {
            "db_path": cls.DATABASE_PATH,
            "timeout": cls.DATABASE_TIMEOUT,
            "upload_dir": cls.UPLOAD_DIR
        }
    
    @classmethod
    def get_rag_config(cls) -> Dict[str, Any]:
        """Lấy cấu hình RAG."""
        return {
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
            "top_k": cls.RAG_TOP_K,
            "batch_size": cls.RAG_BATCH_SIZE,
            "index_path": cls.FAISS_INDEX_PATH,
            "mapping_path": cls.CHUNK_MAPPING_PATH,
            "supported_extensions": cls.SUPPORTED_EXTENSIONS
        }
    
    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """Lấy cấu hình LLM."""
        return {
            "api_key": cls.GOOGLE_API_KEY,
            "model": cls.LLM_MODEL,
            "temperature": cls.LLM_TEMPERATURE
        }
    
    @classmethod
    def get_server_config(cls) -> Dict[str, Any]:
        """Lấy cấu hình server."""
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "debug": cls.DEBUG,
            "cors_origins": cls.CORS_ORIGINS
        } 