from typing import Dict, List, Optional, Any
import sqlite3
import threading
import json
from datetime import datetime
from contextlib import contextmanager


class ConversationMemory:
    """Model để quản lý memory của các cuộc hội thoại.
    
    Mô hình này lưu trữ các thông tin quan trọng (entity) được trích xuất từ hội thoại,
    cho phép chatbot "ghi nhớ" và sử dụng lại thông tin này trong quá trình hội thoại.
    
    Attributes:
        db_path: Đường dẫn đến file database
    """
    
    def __init__(self, db_path: str = "vector_store.db") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._ensure_table_exists()
    
    @contextmanager
    def get_connection(self):
        """Context manager để quản lý database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def _ensure_table_exists(self) -> None:
        """Đảm bảo các bảng cần thiết đã tồn tại trong database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tạo bảng memory_entities nếu chưa tồn tại
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memory_entities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        entity_value TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(conversation_id, entity_type)
                    )
                """)
                
                # Tạo bảng memory_facts nếu chưa tồn tại
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memory_facts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL,
                        fact TEXT NOT NULL,
                        source_message_id INTEGER,
                        confidence REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(conversation_id, fact)
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            print(f"Lỗi khi tạo bảng memory: {str(e)}")
    
    def save_entity(self, conversation_id: str, entity_type: str, entity_value: str, 
                   confidence: float = 1.0) -> bool:
        """Lưu hoặc cập nhật một entity cho một cuộc hội thoại.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            entity_type: Loại entity (name, age, location, preference, etc.)
            entity_value: Giá trị của entity
            confidence: Mức độ tin cậy (0.0 - 1.0)
            
        Returns:
            True nếu lưu thành công, False nếu có lỗi
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Kiểm tra xem entity đã tồn tại chưa
                cursor.execute("""
                    SELECT * FROM memory_entities 
                    WHERE conversation_id = ? AND entity_type = ?
                """, (conversation_id, entity_type))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Cập nhật nếu giá trị mới có confidence cao hơn
                    if confidence >= existing["confidence"]:
                        cursor.execute("""
                            UPDATE memory_entities
                            SET entity_value = ?, confidence = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE conversation_id = ? AND entity_type = ?
                        """, (entity_value, confidence, conversation_id, entity_type))
                else:
                    # Thêm mới nếu chưa tồn tại
                    cursor.execute("""
                        INSERT INTO memory_entities 
                        (conversation_id, entity_type, entity_value, confidence)
                        VALUES (?, ?, ?, ?)
                    """, (conversation_id, entity_type, entity_value, confidence))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Lỗi khi lưu entity: {str(e)}")
            return False
    
    def save_fact(self, conversation_id: str, fact: str, 
                 source_message_id: Optional[int] = None,
                 confidence: float = 1.0) -> bool:
        """Lưu một fact mới từ cuộc hội thoại.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            fact: Nội dung fact cần lưu
            source_message_id: ID của message chứa fact này (nếu có)
            confidence: Mức độ tin cậy (0.0 - 1.0)
            
        Returns:
            True nếu lưu thành công, False nếu có lỗi
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Kiểm tra xem fact đã tồn tại chưa
                cursor.execute("""
                    SELECT * FROM memory_facts
                    WHERE conversation_id = ? AND fact = ?
                """, (conversation_id, fact))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO memory_facts
                        (conversation_id, fact, source_message_id, confidence)
                        VALUES (?, ?, ?, ?)
                    """, (conversation_id, fact, source_message_id, confidence))
                    
                    conn.commit()
                
                return True
                
        except Exception as e:
            print(f"Lỗi khi lưu fact: {str(e)}")
            return False
    
    def get_entities(self, conversation_id: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lấy tất cả entities của một cuộc hội thoại, có thể lọc theo loại.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            entity_type: Loại entity cần lọc (nếu có)
            
        Returns:
            Danh sách các entities đã tìm thấy
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if entity_type:
                    cursor.execute("""
                        SELECT * FROM memory_entities
                        WHERE conversation_id = ? AND entity_type = ?
                        ORDER BY updated_at DESC
                    """, (conversation_id, entity_type))
                else:
                    cursor.execute("""
                        SELECT * FROM memory_entities
                        WHERE conversation_id = ?
                        ORDER BY updated_at DESC
                    """, (conversation_id,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            print(f"Lỗi khi lấy entities: {str(e)}")
            return []
    
    def get_facts(self, conversation_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Lấy các facts được lưu trữ từ một cuộc hội thoại.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            limit: Số lượng facts tối đa cần lấy
            
        Returns:
            Danh sách các facts đã tìm thấy
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM memory_facts
                    WHERE conversation_id = ?
                    ORDER BY confidence DESC, created_at DESC
                    LIMIT ?
                """, (conversation_id, limit))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            print(f"Lỗi khi lấy facts: {str(e)}")
            return []
    
    def get_entity_value(self, conversation_id: str, entity_type: str) -> Optional[str]:
        """Lấy giá trị của một entity cụ thể.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            entity_type: Loại entity cần lấy
            
        Returns:
            Giá trị của entity hoặc None nếu không tìm thấy
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT entity_value FROM memory_entities
                    WHERE conversation_id = ? AND entity_type = ?
                """, (conversation_id, entity_type))
                
                result = cursor.fetchone()
                return result["entity_value"] if result else None
                
        except Exception as e:
            print(f"Lỗi khi lấy giá trị entity: {str(e)}")
            return None
    
    def clear_conversation_memory(self, conversation_id: str) -> bool:
        """Xóa tất cả dữ liệu memory của một cuộc hội thoại.
        
        Args:
            conversation_id: ID của cuộc hội thoại cần xóa memory
            
        Returns:
            True nếu xóa thành công, False nếu có lỗi
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM memory_entities 
                    WHERE conversation_id = ?
                """, (conversation_id,))
                
                cursor.execute("""
                    DELETE FROM memory_facts
                    WHERE conversation_id = ?
                """, (conversation_id,))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Lỗi khi xóa conversation memory: {str(e)}")
            return False
