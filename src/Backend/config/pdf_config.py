"""
Cấu hình cho việc đọc PDF
"""
import os
from dotenv import load_dotenv

load_dotenv()

class PDFConfig:
    """Cấu hình cho PDF reader."""
    
    # Mặc định sử dụng PyMuPDF (fast mode)
    USE_FAST_PDF_READER = os.getenv("USE_FAST_PDF_READER", "true").lower() == "true"
    
    # Fallback timeout cho docling (milliseconds)
    DOCLING_TIMEOUT = int(os.getenv("DOCLING_TIMEOUT", "30000"))
    
    @classmethod
    def get_pdf_reader_mode(cls) -> str:
        """Lấy thông tin về mode đọc PDF hiện tại."""
        return "PyMuPDF (Fast)" if cls.USE_FAST_PDF_READER else "Docling (Accurate)"
    
    @classmethod
    def set_fast_mode(cls, enabled: bool = True) -> None:
        """Thiết lập fast mode cho PDF reader."""
        cls.USE_FAST_PDF_READER = enabled
        print(f"Đã {'bật' if enabled else 'tắt'} fast PDF reader mode")
    
    @classmethod
    def get_current_config(cls) -> dict:
        """Lấy cấu hình hiện tại."""
        return {
            "use_fast_pdf_reader": cls.USE_FAST_PDF_READER,
            "docling_timeout": cls.DOCLING_TIMEOUT,
            "current_mode": cls.get_pdf_reader_mode()
        } 