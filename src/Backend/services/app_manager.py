import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from config.app_config import AppConfig
from services.vector_db import VectorDBService
from services.rag.rag import RAGService
from services.llm.generator import GeneratorService
from services.web.service import WebSearchService
from services.conversation.service import ConversationService
from services.api_manager import ApiManager

logger = logging.getLogger(__name__)

def safe_log(level, message):
    """Log message với encoding an toàn, hỗ trợ tiếng Việt."""
    try:
        getattr(logger, level)(message)
    except UnicodeEncodeError:
        import unicodedata
        safe_message = unicodedata.normalize('NFKD', message).encode('ascii', 'ignore').decode('ascii')
        getattr(logger, level)(safe_message)

class AppManager:
    """Manager trung tâm cho toàn bộ ứng dụng."""
    
    def __init__(self):
        self.config = AppConfig()
        self.services = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Khởi tạo tất cả services."""
        try:
            safe_log('info', "Bắt đầu khởi tạo ứng dụng...")
            
            validation = self.config.validate_config()
            if not validation["valid"]:
                safe_log('error', f"Cấu hình không hợp lệ: {validation['errors']}")
                return False
            
            await self._init_database_service()
            await self._init_rag_service()
            await self._init_llm_service()
            await self._init_web_service()
            await self._init_conversation_service()
            await self._init_api_service()
            
            await self._auto_sync_files()
            
            self._initialized = True
            safe_log('info', "Khởi tạo ứng dụng thành công!")
            return True
            
        except Exception as e:
            safe_log('error', f"Lỗi khởi tạo ứng dụng: {str(e)}")
            return False
    
    async def _init_database_service(self):
        """Khởi tạo database service."""
        safe_log('info', "Khởi tạo Database Service...")
        
        db_config = self.config.get_database_config()
        self.services['database'] = VectorDBService(
            db_path=db_config['db_path'],
            upload_dir=db_config['upload_dir'],
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP
        )
        
        safe_log('info', "Database Service đã sẵn sàng")
    
    async def _init_rag_service(self):
        """Khởi tạo RAG service."""
        safe_log('info', "Khởi tạo RAG Service...")
        
        self.services['rag'] = RAGService(upload_dir=self.config.UPLOAD_DIR)
        
        safe_log('info', "RAG Service đã sẵn sàng")
    
    async def _init_llm_service(self):
        """Khởi tạo LLM service."""
        safe_log('info', "Khởi tạo LLM Service...")
        
        self.services['llm'] = GeneratorService()
        
        safe_log('info', "LLM Service đã sẵn sàng")
    
    async def _init_web_service(self):
        """Khởi tạo Web Search service."""
        safe_log('info', "Khởi tạo Web Search Service...")
        
        self.services['web'] = WebSearchService()
        
        safe_log('info', "Web Search Service đã sẵn sàng")
    
    async def _init_conversation_service(self):
        """Khởi tạo Conversation service."""
        safe_log('info', "Khởi tạo Conversation Service...")
        
        self.services['conversation'] = ConversationService()
        
        safe_log('info', "Conversation Service đã sẵn sàng")
    
    async def _init_api_service(self):
        """Khởi tạo API Manager."""
        safe_log('info', "Khởi tạo API Manager...")
        
        self.services['api'] = ApiManager()
        
        safe_log('info', "API Manager đã sẵn sàng")
    
    async def _auto_sync_files(self):
        """Tự động đồng bộ file upload."""
        try:
            safe_log('info', "Kiểm tra và đồng bộ file upload...")
            
            rag_service = self.services.get('rag')
            if rag_service:
                files_updated = await rag_service.check_and_update_files()
                
                if files_updated:
                    safe_log('info', "Đã tự động đồng bộ file upload vào database")
                else:
                    safe_log('info', "Không có file mới cần đồng bộ")
            
        except Exception as e:
            safe_log('error', f"Lỗi khi đồng bộ file startup: {str(e)}")
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Lấy service theo tên."""
        return self.services.get(service_name)
    
    def get_all_services(self) -> Dict[str, Any]:
        """Lấy tất cả services."""
        return self.services.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Kiểm tra sức khỏe của tất cả services."""
        health_status = {
            "status": "healthy" if self._initialized else "initializing",
            "services": {},
            "config_valid": self.config.validate_config()["valid"]
        }
        
        for service_name, service in self.services.items():
            try:
                if hasattr(service, 'health_check'):
                    service_health = await service.health_check()
                else:
                    service_health = {"status": "running", "available": True}
                
                health_status["services"][service_name] = service_health
                
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "error",
                    "error": str(e),
                    "available": False
                }
        
        return health_status
    
    async def shutdown(self):
        """Tắt tất cả services."""
        safe_log('info', "Đang tắt ứng dụng...")
        
        for service_name, service in self.services.items():
            try:
                if hasattr(service, 'shutdown'):
                    await service.shutdown()
                safe_log('info', f"Đã tắt {service_name} service")
            except Exception as e:
                safe_log('error', f"Lỗi khi tắt {service_name}: {str(e)}")
        
        self.services.clear()
        self._initialized = False
        safe_log('info', "Ứng dụng đã tắt hoàn toàn")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Lấy thông tin hệ thống."""
        return {
            "app_name": "Agent System",
            "version": "1.0.0",
            "initialized": self._initialized,
            "services_count": len(self.services),
            "config": self.config.get_all_config(),
            "services_list": list(self.services.keys())
        }

app_manager = AppManager()

@asynccontextmanager
async def get_app_manager():
    """Context manager để sử dụng app manager."""
    if not app_manager._initialized:
        await app_manager.initialize()
    
    try:
        yield app_manager
    finally:
        pass