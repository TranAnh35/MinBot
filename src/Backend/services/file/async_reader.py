import os
from fastapi import UploadFile
from .base_reader import BaseFileReader
from config.pdf_config import PDFConfig
import io
import asyncio


class AsyncFileReader(BaseFileReader):
    """Unified async file reader cho cả UploadFile và file paths."""
    
    def __init__(self):
        # Sử dụng cấu hình từ PDFConfig
        super().__init__(use_fast_pdf_reader=PDFConfig.USE_FAST_PDF_READER)

    async def read_uploaded_file(self, file: UploadFile) -> str:
        """Đọc nội dung file được upload từ FastAPI."""
        if not file.filename:
            raise ValueError("Filename không được để trống")
        
        try:
            extension = self.get_file_extension(file.filename)
            
            if not self.is_supported_extension(file.filename):
                content = await file.read()
                return self.read_text_content(content)
            
            if extension == '.pdf':
                content = await file.read()
                return self.read_pdf_content(content)
            elif extension in ('.doc', '.docx'):
                await file.seek(0)
                return self.read_docx_content(file.file)
            elif extension in ('.yaml', '.yml'):
                content = await file.read()
                return self.read_yaml_content(content)
            elif extension in ('.txt', '.md'):
                content = await file.read()
                return self.read_text_content(content)
            else:
                content = await file.read()
                return self.read_text_content(content)
                
        except Exception as e:
            raise Exception(f"Không thể đọc file {file.filename}: {str(e)}")
        finally:
            await file.close()

    async def read_file_from_path(self, file_path: str) -> str:
        """Đọc nội dung file từ đường dẫn (async version)."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        file_name = os.path.basename(file_path)
        extension = self.get_file_extension(file_name)
        
        if not self.is_supported_extension(file_name):
            return await self._read_text_file_async(file_path)
        
        if extension == '.pdf':
            return self.read_pdf_content(file_path)
        elif extension in ('.doc', '.docx'):
            return self.read_docx_content(file_path)
        elif extension in ('.yaml', '.yml'):
            return self.read_yaml_content(file_path)
        elif extension in ('.txt', '.md'):
            return await self._read_text_file_async(file_path)
        else:
            return await self._read_text_file_async(file_path)

    async def _read_text_file_async(self, file_path: str) -> str:
        """Đọc file text bất đồng bộ với multiple encodings."""
        def _read_sync(path: str, encoding: str) -> str:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        
        for encoding in self.encodings:
            try:
                # Sử dụng asyncio.to_thread để chạy sync I/O trong thread pool
                return await asyncio.to_thread(_read_sync, file_path, encoding)
            except UnicodeDecodeError:
                continue
        raise Exception("Không thể đọc file với các encoding đã thử")

    async def read_file(self, source) -> str:
        """Universal method để đọc file từ bất kỳ source nào."""
        if isinstance(source, UploadFile):
            return await self.read_uploaded_file(source)
        elif isinstance(source, str):
            return await self.read_file_from_path(source)
        else:
            raise ValueError("Source phải là UploadFile hoặc file path string") 