import sqlite3
import threading
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager


class ConversationDatabaseManager:
    """Quản lý các operations liên quan đến conversations trong database."""
    
    def __init__(self, db_path: str = "vector_store.db") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()

    @contextmanager
    def get_connection(self):
        """Context manager để quản lý database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Tạo một conversation mới trong database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations (id, user_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (conversation_id, user_id, "Cuộc trò chuyện mới"))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Conversation ID đã tồn tại
            return False
        except Exception as e:
            print(f"Lỗi khi tạo conversation: {str(e)}")
            return False

    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Thêm một message vào conversation."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
                if not cursor.fetchone():
                    return False
                
                cursor.execute("""
                    INSERT INTO messages (conversation_id, role, content, timestamp)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (conversation_id, role, content))
                
                cursor.execute("""
                    UPDATE conversations 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (conversation_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Lỗi khi thêm message: {str(e)}")
            return False

    def rename_conversation(self, conversation_id: str, title: str) -> bool:
        """Đổi tên một conversation."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE conversations 
                    SET title = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (title, conversation_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return True
                return False
        except Exception as e:
            print(f"Lỗi khi đổi tên conversation: {str(e)}")
            return False

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin conversation theo ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, user_id, title, created_at, updated_at
                    FROM conversations 
                    WHERE id = ?
                """, (conversation_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                cursor.execute("""
                    SELECT role, content, timestamp
                    FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """, (conversation_id,))
                
                messages = []
                for msg_row in cursor.fetchall():
                    messages.append({
                        "role": msg_row["role"],
                        "content": msg_row["content"],
                        "timestamp": msg_row["timestamp"]
                    })
                
                return {
                    "conversation_id": row["id"],
                    "user_id": row["user_id"],
                    "title": row["title"],
                    "messages": messages,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
        except Exception as e:
            print(f"Lỗi khi lấy conversation: {str(e)}")
            return None

    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy lịch sử messages của một conversation."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
                if not cursor.fetchone():
                    return []
                
                cursor.execute("""
                    SELECT role, content, timestamp
                    FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (conversation_id, limit))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"]
                    })
                
                return list(reversed(messages))
        except Exception as e:
            print(f"Lỗi khi lấy conversation history: {str(e)}")
            return []

    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Liệt kê tất cả conversations của một user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.id, c.user_id, c.title, c.created_at, c.updated_at,
                           m.content as last_message_content
                    FROM conversations c
                    LEFT JOIN (
                        SELECT conversation_id, content,
                               ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY timestamp DESC) as rn
                        FROM messages
                    ) m ON c.id = m.conversation_id AND m.rn = 1
                    WHERE c.user_id = ?
                    ORDER BY c.updated_at DESC
                """, (user_id,))
                
                conversations = []
                for row in cursor.fetchall():
                    last_message = row["last_message_content"] or ""
                    preview = last_message[:50] + "..." if len(last_message) > 50 else last_message
                    if not preview:
                        preview = "Empty conversation"
                    
                    conversations.append({
                        "conversation_id": row["id"],
                        "user_id": row["user_id"],
                        "title": row["title"],
                        "preview": preview,
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"]
                    })
                
                return conversations
        except Exception as e:
            print(f"Lỗi khi liệt kê conversations: {str(e)}")
            return []

    def delete_conversation(self, conversation_id: str) -> bool:
        """Xóa một conversation và tất cả messages của nó."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return True
                return False
        except Exception as e:
            print(f"Lỗi khi xóa conversation: {str(e)}")
            return False

    def auto_update_conversation_title(self, conversation_id: str, user_message: str) -> bool:
        """Tự động cập nhật title của conversation dựa trên message đầu tiên."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT title FROM conversations 
                    WHERE id = ? AND title = 'Cuộc trò chuyện mới'
                """, (conversation_id,))
                
                if cursor.fetchone():
                    new_title = user_message[:30] + ("..." if len(user_message) > 30 else "")
                    cursor.execute("""
                        UPDATE conversations 
                        SET title = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (new_title, conversation_id))
                    conn.commit()
                    return True
                return False
        except Exception as e:
            print(f"Lỗi khi cập nhật title: {str(e)}")
            return False

    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """Lấy thống kê conversations của user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
                total_conversations = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(m.id) 
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = ?
                """, (user_id,))
                total_messages = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT updated_at 
                    FROM conversations 
                    WHERE user_id = ?
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, (user_id,))
                last_activity = cursor.fetchone()
                last_activity = last_activity[0] if last_activity else None
                
                return {
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "last_activity": last_activity
                }
        except Exception as e:
            print(f"Lỗi khi lấy stats: {str(e)}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "last_activity": None
            } 