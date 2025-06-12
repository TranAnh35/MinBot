from fastapi import APIRouter, UploadFile, File, HTTPException
from services.file.storage import FileStorage
from services.file.async_reader import AsyncFileReader
from services.vector_db import VectorDBService
from services.rag.rag import RAGService
from config.pdf_config import PDFConfig
from urllib.parse import unquote
from typing import Dict, Any, List

router = APIRouter()
vector_db = VectorDBService()
file_storage = FileStorage()
async_file_reader = AsyncFileReader()
rag_service = RAGService()

@router.post("/upload", response_model=Dict[str, Any])
async def upload_file(file: UploadFile = File(...)):
    """Tải lên một file mới."""
    try:
        file_path = file_storage.save_file(file)
        await rag_service.check_and_update_files()
        return {"message": "Tải file lên thành công và đã được xử lý", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tải file lên: {str(e)}")

@router.get("/files", response_model=Dict[str, List[Dict[str, Any]]])
async def get_files():
    """Lấy danh sách tất cả các file đã tải lên."""
    return {"files": file_storage.list_files()}

@router.delete("/delete/{file_name}", response_model=Dict[str, str])
async def delete_uploaded_file(file_name: str):
    """Xóa một file đã tải lên."""
    decoded_filename = unquote(file_name)
    
    # Xóa file khỏi hệ thống
    if file_storage.delete_file(decoded_filename):
        # Xóa dữ liệu khỏi database
        vector_db.delete_file_from_db(decoded_filename)
        return {"message": "Đã xóa file thành công"}
    raise HTTPException(status_code=404, detail="Không tìm thấy file")

@router.post("/read", response_model=Dict[str, Any])
async def read_file(file: UploadFile = File(...)):
    """Đọc nội dung của file được tải lên."""
    try:
        content = await async_file_reader.read_uploaded_file(file)
        return {"file_name": file.filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file: {str(e)}")

@router.get("/pdf-config", response_model=Dict[str, Any])
async def get_pdf_config():
    """Lấy cấu hình hiện tại của PDF reader."""
    return PDFConfig.get_current_config()

@router.post("/pdf-config", response_model=Dict[str, str])
async def set_pdf_config(use_fast_reader: bool):
    """Thiết lập mode đọc PDF.
    
    Args:
        use_fast_reader (bool): True để sử dụng PyMuPDF (nhanh), False để sử dụng docling (chính xác)
    """
    PDFConfig.set_fast_mode(use_fast_reader)
    return {
        "message": f"Đã chuyển sang mode: {PDFConfig.get_pdf_reader_mode()}",
        "current_mode": PDFConfig.get_pdf_reader_mode()
    }