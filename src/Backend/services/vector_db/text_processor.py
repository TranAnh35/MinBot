from typing import List


class TextProcessor:
    """Xử lý việc chia văn bản thành các chunks."""
    
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.split_chars = ['.', '!', '?', '\n', ',', ';', ' ']

    def split_text(self, text: str) -> List[str]:
        """Tách văn bản thành các đoạn (chunks) với kích thước và độ chồng lấn xác định."""
        if not text:
            return []
            
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            
            if end >= text_length:
                if start < text_length:
                    chunks.append(text[start:].strip())
                break
                
            split_pos = self._find_optimal_split_point(text, start, end)
            
            if split_pos <= start:
                split_pos = end
                
            chunk = text[start:split_pos].strip()
            if chunk:
                chunks.append(chunk)
                
            start = max(split_pos - self.chunk_overlap, start + 1)
            
        return chunks

    def _find_optimal_split_point(self, text: str, start: int, end: int) -> int:
        """Tìm điểm tách tối ưu trong khoảng văn bản đã cho."""
        for split_char in self.split_chars:
            pos = text.rfind(split_char, start, end + 1)
            if pos > start:
                return pos + 1  
                
        return end

    def set_chunk_size(self, chunk_size: int) -> None:
        """Thiết lập kích thước chunk mới."""
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        self.chunk_size = chunk_size

    def set_chunk_overlap(self, chunk_overlap: int) -> None:
        """Thiết lập độ chồng lấn chunk mới."""
        if chunk_overlap < 0:
            raise ValueError("Chunk overlap must be non-negative")
        if chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        self.chunk_overlap = chunk_overlap

    def get_chunk_info(self) -> dict:
        """Lấy thông tin về cấu hình chunking hiện tại."""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "split_chars": self.split_chars
        } 