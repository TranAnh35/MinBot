import os
import asyncio
from typing import Set, List
from pathlib import Path

from services.vector_db.database_manager import DatabaseManager
from services.vector_db.text_processor import TextProcessor
from .async_reader import AsyncFileReader


class AsyncFileProcessor:
    """Async file processor cho việc xử lý file và synchronization."""
    
    def __init__(
        self, 
        database_manager: DatabaseManager,
        text_processor: TextProcessor,
        upload_dir: str = "upload"
    ) -> None:
        self.database_manager = database_manager
        self.text_processor = text_processor
        self.upload_dir = upload_dir
        self.file_reader = AsyncFileReader()
        self.valid_extensions = {'.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml'}

    async def process_file(self, file_path: str) -> None:
        """Xử lý file và lưu vào database nếu nội dung thay đổi (async)."""
        try:
            file_name = os.path.basename(file_path)
            content = await self.file_reader.read_file_from_path(file_path)
            
            has_changed, file_id = self.database_manager.check_file_changed(
                file_name, len(content)
            )
            
            if not has_changed:
                return  
            
            chunks = self.text_processor.split_text(content)
            
            file_id = self.database_manager.update_file_metadata(
                file_name, len(content)
            )
            
            self.database_manager.update_file_chunks(file_id, chunks)
            
        except Exception as e:
            print(f"Lỗi khi xử lý file {file_path}: {str(e)}")
            raise

    def get_db_files(self) -> Set[str]:
        """Lấy danh sách tên các file đã lưu trong database."""
        with self.database_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM files")
            return {row[0] for row in cursor.fetchall()}
    
    def get_uploaded_files(self) -> Set[str]:
        """Lấy danh sách các file trong thư mục upload."""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir, exist_ok=True)
            return set()
            
        return {
            file for file in os.listdir(self.upload_dir)
            if os.path.splitext(file)[1].lower() in self.valid_extensions
        }
    
    def cleanup_missing_files(self, db_files: Set[str], uploaded_files: Set[str]) -> None:
        """Xóa dữ liệu của các file không còn tồn tại trong thư mục upload."""
        files_to_delete = db_files - uploaded_files
        for file_name in files_to_delete:
            try:
                self.database_manager.delete_file_from_db(file_name)
                print(f"Đã xóa dữ liệu của file không còn tồn tại: {file_name}")
            except Exception as e:
                print(f"Lỗi khi xóa dữ liệu của file {file_name}: {str(e)}")
    
    async def process_uploaded_files(self, uploaded_files: Set[str]) -> None:
        """Xử lý các file mới hoặc đã thay đổi trong thư mục upload (async)."""
        tasks = []
        for file_name in uploaded_files:
            file_path = os.path.join(self.upload_dir, file_name)
            tasks.append(self._process_single_file(file_path, file_name))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_file(self, file_path: str, file_name: str) -> None:
        """Xử lý một file đơn lẻ."""
        try:
            await self.process_file(file_path)
            print(f"Đã xử lý file: {file_name}")
        except Exception as e:
            print(f"Lỗi khi xử lý file {file_name}: {str(e)}")
    
    async def update_from_upload(self) -> None:
        """Đồng bộ dữ liệu từ thư mục upload vào VectorDB (async)."""
        try:
            db_files = self.get_db_files()
            uploaded_files = self.get_uploaded_files()
            
            self.cleanup_missing_files(db_files, uploaded_files)
            await self.process_uploaded_files(uploaded_files)
                    
        except Exception as e:
            print(f"Lỗi khi đồng bộ dữ liệu: {str(e)}")

    def delete_file(self, file_name: str) -> None:
        """Xóa file khỏi cả database và filesystem."""
        try:
            # Xóa khỏi database
            self.database_manager.delete_file_from_db(file_name)
            
            # Xóa khỏi filesystem nếu tồn tại
            file_path = os.path.join(self.upload_dir, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Đã xóa file {file_name} khỏi filesystem")
                
        except Exception as e:
            print(f"Lỗi khi xóa file {file_name}: {str(e)}")
            raise

    def get_supported_extensions(self) -> Set[str]:
        """Lấy danh sách các extension được hỗ trợ."""
        return self.valid_extensions.copy()

    def add_supported_extension(self, extension: str) -> None:
        """Thêm extension mới được hỗ trợ."""
        if not extension.startswith('.'):
            extension = '.' + extension
        self.valid_extensions.add(extension.lower())

    def remove_supported_extension(self, extension: str) -> None:
        """Xóa extension khỏi danh sách hỗ trợ."""
        if not extension.startswith('.'):
            extension = '.' + extension
        self.valid_extensions.discard(extension.lower()) 