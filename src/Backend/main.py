from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api import rag_routes, gen_routes, file_routes, web_routes, api_key_routes, conversation_routes
from api.system import routes as system_routes
from services.vector_db.database_manager import DatabaseManager
from services.app_manager import app_manager
from config.app_config import AppConfig
import logging
import sys
import os

config = AppConfig()

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

db_manager = DatabaseManager(config.DATABASE_PATH)
db_manager.init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager để quản lý startup và shutdown events."""
    try:
        logger.info("Khởi động Agent System...")
        
        success = await app_manager.initialize()
        
        if success:
            logger.info("Agent System đã sẵn sàng!")
        else:
            logger.error("Khởi tạo ứng dụng thất bại!")
            
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng khi khởi động: {str(e)}")
    
    yield
    
    await app_manager.shutdown()

app = FastAPI(
    title="Agent System",
    version="1.0.0",
    debug=config.DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_routes.router, prefix="/rag", tags=["RAG"])
app.include_router(file_routes.router, prefix="/files", tags=["Files"])
app.include_router(web_routes.router, prefix="/web", tags=["WebSearch"])
app.include_router(gen_routes.router, prefix="/generate", tags=["Generative Content"])
app.include_router(api_key_routes.router, prefix="/api-key", tags=["API Key"])
app.include_router(conversation_routes.router, prefix="/conversations", tags=["Conversations"])
app.include_router(system_routes.router, prefix="/system", tags=["System Management"])

@app.get("/")
def read_root():
    return {
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

@app.get("/health")
async def health_check():
    """Health check endpoint để kiểm tra trạng thái ứng dụng."""
    try:
        health_status = await app_manager.health_check()
        return health_status
    except Exception as e:
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "database": "Unknown",
            "version": "1.0.0"
        }

@app.get("/system/info")
async def get_system_info():
    """Lấy thông tin chi tiết về hệ thống."""
    return app_manager.get_system_info()

@app.get("/system/config")
async def get_system_config():
    """Lấy cấu hình hệ thống (ẩn sensitive data)."""
    config_data = config.get_all_config()
    
    sensitive_keys = ['GOOGLE_API_KEY', 'GOOGLE_SEARCH_API_KEY']
    for key in sensitive_keys:
        if key in config_data and config_data[key]:
            config_data[key] = "***HIDDEN***"
    
    return {
        "config": config_data,
        "validation": config.validate_config()
    }