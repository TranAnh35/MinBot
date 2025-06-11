import os
import tempfile
import yaml
from typing import Union, BinaryIO
import io
from config.pdf_config import PDFConfig


class BaseFileReader:
    """Base class chứa logic chung để đọc các loại file khác nhau."""
    
    def __init__(self, use_fast_pdf_reader=None):
        self._converter = None
        # Sử dụng config nếu không được override
        self.use_fast_pdf_reader = use_fast_pdf_reader if use_fast_pdf_reader is not None else PDFConfig.USE_FAST_PDF_READER
        self.encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    
    @property
    def converter(self):
        """Lazy loading DocumentConverter để tránh import error khi không cần thiết."""
        if self._converter is None:
            from docling.document_converter import DocumentConverter
            self._converter = DocumentConverter()
        return self._converter

    def read_pdf_content(self, file_source: Union[str, bytes]) -> str:
        """Đọc nội dung PDF từ file path hoặc bytes."""
        if self.use_fast_pdf_reader:
            return self._read_pdf_with_pymupdf(file_source)
        else:
            return self._read_pdf_with_docling(file_source)
    
    def _read_pdf_with_pymupdf(self, file_source: Union[str, bytes]) -> str:
        """Đọc PDF sử dụng PyMuPDF (nhanh hơn)."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("PyMuPDF không được cài đặt, chuyển về docling...")
            return self._read_pdf_with_docling(file_source)
        except Exception as e:
            print(f"Lỗi import PyMuPDF: {e}, chuyển về docling...")
            return self._read_pdf_with_docling(file_source)
        
        try:
            if isinstance(file_source, str):
                # Đọc từ file path
                doc = fitz.open(file_source)
            else:
                # Đọc từ bytes
                doc = fitz.open(stream=file_source, filetype="pdf")
            
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
                text += "\n"  # Thêm newline giữa các trang
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            print(f"Lỗi khi đọc PDF với PyMuPDF: {str(e)}, chuyển về docling...")
            return self._read_pdf_with_docling(file_source)
    
    def _read_pdf_with_docling(self, file_source: Union[str, bytes]) -> str:
        """Đọc PDF sử dụng docling (chính xác hơn nhưng chậm hơn)."""
        if isinstance(file_source, str):
            # Đọc từ file path
            result = self.converter.convert(file_source)
            return result.document.export_to_markdown()
        else:
            # Đọc từ bytes
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_source)
                temp_file_path = temp_file.name
            
            try:
                result = self.converter.convert(temp_file_path)
                return result.document.export_to_markdown()
            finally:
                os.unlink(temp_file_path)

    def read_docx_content(self, file_source: Union[str, BinaryIO]) -> str:
        """Đọc nội dung DOCX từ file path hoặc file object."""
        from docx import Document
        doc = Document(file_source)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    def read_yaml_content(self, content: Union[str, bytes]) -> str:
        """Đọc nội dung YAML từ string hoặc bytes."""
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        elif isinstance(content, str) and os.path.exists(content):
            # Nếu là file path
            with open(content, 'r', encoding='utf-8') as f:
                content = f.read()
        
        data = yaml.safe_load(content)
        return str(data)

    def read_text_content(self, content: Union[str, bytes]) -> str:
        """Đọc nội dung text từ string, bytes hoặc file path."""
        if isinstance(content, str) and os.path.exists(content):
            # Đọc từ file path
            for encoding in self.encodings:
                try:
                    with open(content, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise Exception("Không thể đọc file với các encoding đã thử")
        elif isinstance(content, bytes):
            # Đọc từ bytes
            for encoding in self.encodings:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            raise Exception("Không thể đọc file với các encoding đã thử")
        else:
            # Đã là string
            return content

    def get_file_extension(self, filename: str) -> str:
        """Lấy phần mở rộng file."""
        return os.path.splitext(filename.lower())[1]

    def is_supported_extension(self, filename: str) -> bool:
        """Kiểm tra xem file extension có được hỗ trợ không."""
        supported_extensions = {'.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml', '.md'}
        return self.get_file_extension(filename) in supported_extensions
    
    def set_pdf_reader_mode(self, use_fast_reader: bool) -> None:
        """Thiết lập mode đọc PDF.
        
        Args:
            use_fast_reader (bool): True để sử dụng PyMuPDF (nhanh), False để sử dụng docling (chính xác)
        """
        self.use_fast_pdf_reader = use_fast_reader
        print(f"Đã chuyển sang mode đọc PDF: {'PyMuPDF (Fast)' if use_fast_reader else 'Docling (Accurate)'}")
    
    def get_pdf_reader_mode(self) -> str:
        """Lấy thông tin về mode đọc PDF hiện tại."""
        return "PyMuPDF (Fast)" if self.use_fast_pdf_reader else "Docling (Accurate)" 