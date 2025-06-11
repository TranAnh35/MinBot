import os
import threading
from typing import List, Tuple, Optional

from .database_manager import DatabaseManager
from .text_processor import TextProcessor
from services.file import get_async_file_processor


class VectorDBService:
    """
    Service chính để quản lý Vector Database với dependency injection.
    Tuân thủ Single Responsibility Principle bằng cách ủy quyền cho các components chuyên biệt.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Thread-safe Singleton implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(VectorDBService, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        db_path: str = "vector_store.db",
        upload_dir: str = "upload",
        chunk_size: int = 2000,
        chunk_overlap: int = 200
    ) -> None:
        if hasattr(self, '_initialized'):
            return
            
        self.db_path = db_path
        self.upload_dir = upload_dir
        
        self.database_manager = DatabaseManager(db_path)
        self.text_processor = TextProcessor(chunk_size, chunk_overlap)
        AsyncFileProcessor = get_async_file_processor()
        self.file_processor = AsyncFileProcessor(
            self.database_manager, 
            self.text_processor, 
            upload_dir
        )
        
        # Khởi tạo database nếu chưa tồn tại
        if not os.path.exists(db_path):
            print("Database không tồn tại, tạo mới...")
            self.database_manager.init_db()
            
        self._initialized = True

    def init_db(self) -> None:
        """Khởi tạo cơ sở dữ liệu SQLite."""
        return self.database_manager.init_db()

    def reset_db(self) -> None:
        """Xóa và tạo lại cơ sở dữ liệu từ đầu."""
        return self.database_manager.reset_db()

    def split_text(self, text: str) -> List[str]:
        """Tách văn bản thành các đoạn (chunks)."""
        return self.text_processor.split_text(text)

    def set_chunk_size(self, chunk_size: int) -> None:
        """Thiết lập kích thước chunk mới."""
        return self.text_processor.set_chunk_size(chunk_size)

    def set_chunk_overlap(self, chunk_overlap: int) -> None:
        """Thiết lập độ chồng lấn chunk mới."""
        return self.text_processor.set_chunk_overlap(chunk_overlap)

    async def process_file(self, file_path: str) -> None:
        """Xử lý file và lưu vào database nếu nội dung thay đổi."""
        return await self.file_processor.process_file(file_path)

    async def update_from_upload(self) -> None:
        """Đồng bộ dữ liệu từ thư mục upload vào VectorDB."""
        return await self.file_processor.update_from_upload()

    def delete_file_from_db(self, file_name: str) -> None:
        """Xóa dữ liệu của file khỏi database."""
        return self.database_manager.delete_file_from_db(file_name)

    def delete_file(self, file_name: str) -> None:
        """Xóa file khỏi cả database và filesystem."""
        return self.file_processor.delete_file(file_name)

    def get_chunk_by_id(self, doc_id: int) -> Optional[str]:
        """Lấy nội dung chunk dựa trên ID."""
        with self.database_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM chunks WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_all_chunks(self) -> List[Tuple[int, str, str, int]]:
        """Lấy tất cả các chunks từ cơ sở dữ liệu."""
        with self.database_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.content, f.name as source, c.chunk_index
                FROM chunks c
                JOIN files f ON f.id = c.file_id
                ORDER BY f.name, c.chunk_index
            """)
            return cursor.fetchall()

    def get_chunks_by_file(self, file_name: str) -> List[Tuple[int, str, int]]:
        """Lấy tất cả các chunks thuộc về một file cụ thể."""
        with self.database_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.content, c.chunk_index
                FROM chunks c
                JOIN files f ON f.id = c.file_id
                WHERE f.name = ?
                ORDER BY c.chunk_index
            """, (file_name,))
            return cursor.fetchall()

    def get_all_files(self) -> List[Tuple[int, str, int, str, str]]:
        """Lấy danh sách tất cả các file đã được lưu trong database."""
        with self.database_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, size, created_at, updated_at
                FROM files
                ORDER BY name
            """)
            return cursor.fetchall()

    def get_configuration(self) -> dict:
        """Lấy thông tin cấu hình hiện tại."""
        return {
            "db_path": self.db_path,
            "upload_dir": self.upload_dir,
            "text_processor": self.text_processor.get_chunk_info(),
            "supported_extensions": list(self.file_processor.get_supported_extensions())
        }

    def add_supported_extension(self, extension: str) -> None:
        """Thêm extension mới được hỗ trợ."""
        return self.file_processor.add_supported_extension(extension)

    def remove_supported_extension(self, extension: str) -> None:
        """Xóa extension khỏi danh sách hỗ trợ."""
        return self.file_processor.remove_supported_extension(extension)

    def delete_file_data(self, file_name: str) -> None:
        """
        Deprecated: Use delete_file_from_db instead.
        Xóa toàn bộ dữ liệu liên quan đến một file khỏi database.
        """
        import warnings
        warnings.warn(
            "delete_file_data is deprecated, use delete_file_from_db instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.delete_file_from_db(file_name) 