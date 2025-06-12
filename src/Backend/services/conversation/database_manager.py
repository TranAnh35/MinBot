import sqlite3
import threading
import json
import os
import base64
import binascii
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager


class ConversationDatabaseManager:
    """Quản lý các operations liên quan đến conversations trong database."""
    
    def __init__(self, db_path: str = "vector_store.db") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._run_migrations()

    def _run_migrations(self):
        """Chạy các migration cần thiết cho schema database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Kiểm tra xem cột 'attachments' đã tồn tại trong bảng 'messages' chưa
                cursor.execute("PRAGMA table_info(messages)")
                columns = [col[1] for col in cursor.fetchall()]
                if 'attachments' not in columns:
                    cursor.execute("ALTER TABLE messages ADD COLUMN attachments TEXT")
                    print("Migration: Đã thêm cột 'attachments' vào bảng 'messages'.")
                
                conn.commit()
        except Exception as e:
            print(f"Lỗi khi chạy migration: {str(e)}")

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

    def add_message(self, conversation_id: str, role: str, content: str, attachments: Optional[List[Dict]] = None) -> bool:
        """Thêm một message vào conversation và xử lý file đính kèm."""
        try:
            processed_attachments = []
            if attachments:
                # Đường dẫn thư mục để lưu file cho conversation này
                upload_dir = os.path.join("upload", "conversations", conversation_id)
                os.makedirs(upload_dir, exist_ok=True)

                for attachment in attachments:
                    file_content_base64 = attachment.get("content")
                    file_name = attachment.get("name")

                    if file_content_base64 and file_name:
                        try:
                            # Giải mã base64
                            file_content = base64.b64decode(file_content_base64)
                            
                            # Tạo đường dẫn file an toàn
                            safe_filename = "".join(c for c in file_name if c.isalnum() or c in ('.', '_', '-')).rstrip()
                            file_path = os.path.join(upload_dir, safe_filename)

                            # Lưu file
                            with open(file_path, "wb") as f:
                                f.write(file_content)

                            # Lưu đường dẫn thay vì nội dung file
                            processed_attachments.append({
                                "name": safe_filename,
                                "size": attachment.get("size")
                            })
                        except (binascii.Error, IOError) as e: # Catch binascii.Error directly
                            print(f"Lỗi khi xử lý file đính kèm {file_name}: {e}")
                            # Có thể thêm file lỗi vào danh sách để thông báo
                            processed_attachments.append({
                                "name": file_name,
                                "error": f"Failed to save: {e}"
                            })

            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
                if not cursor.fetchone():
                    return False
                
                attachments_json = json.dumps(processed_attachments) if processed_attachments else None

                cursor.execute("""
                    INSERT INTO messages (conversation_id, role, content, timestamp, attachments)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (conversation_id, role, content, attachments_json))
                
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
                    SELECT role, content, timestamp, attachments
                    FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """, (conversation_id,))
                
                messages = []
                for msg_row in cursor.fetchall():
                    attachments = json.loads(msg_row["attachments"]) if msg_row["attachments"] else None
                    messages.append({
                        "role": msg_row["role"],
                        "content": msg_row["content"],
                        "timestamp": msg_row["timestamp"],
                        "attachments": attachments
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

    def get_conversation_history(self, conversation_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Lấy lịch sử messages của một conversation với hỗ trợ pagination (mới nhất trước)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
                if not cursor.fetchone():
                    return []
                
                # Sắp xếp theo timestamp DESC để lấy tin nhắn mới nhất trước
                cursor.execute("""
                    SELECT role, content, timestamp, attachments
                    FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """, (conversation_id, limit, offset))
                
                messages = []
                for row in cursor.fetchall():
                    attachments = json.loads(row["attachments"]) if row["attachments"] else None
                    messages.append({
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                        "attachments": attachments
                    })
                
                # Trả về theo thứ tự thời gian tăng dần để hiển thị
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
                
                # Bắt đầu một transaction
                cursor.execute("BEGIN")

                # Xóa tất cả messages liên quan đến conversation
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                
                # Xóa conversation
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return True
                
                # Nếu không có conversation nào bị xóa (ví dụ: ID không tồn tại), rollback
                conn.rollback()
                return False
        except Exception as e:
            print(f"Lỗi khi xóa conversation: {str(e)}")
            # Không cần rollback vì đã ra khỏi context manager
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
    
    def count_conversation_messages(self, conversation_id: str) -> int:
        """Đếm tổng số messages trong một conversation."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conversation_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Lỗi khi đếm messages: {str(e)}")
            return 0
    
    def get_latest_message(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Lấy message cuối cùng của một conversation."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content, timestamp, attachments
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (conversation_id,))
                row = cursor.fetchone()
                if row:
                    attachments = json.loads(row["attachments"]) if row["attachments"] else None
                    return {
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                        "attachments": attachments
                    }
                return None
        except Exception as e:
            print(f"Lỗi khi lấy message cuối cùng: {str(e)}")
            return None
    
    def get_recent_messages(self, conversation_id: str, count: int = 5) -> List[Dict[str, Any]]:
        """Lấy một vài message gần đây để kiểm tra trùng lặp."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT role, content, timestamp, attachments
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (conversation_id, count))
                
                messages = []
                for row in cursor.fetchall():
                    attachments = json.loads(row["attachments"]) if row["attachments"] else None
                    messages.append({
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                        "attachments": attachments
                    })
                return messages
        except Exception as e:
            print(f"Lỗi khi lấy messages gần đây: {str(e)}")
            return []
    
    def clear_conversation_messages(self, conversation_id: str) -> bool:
        """Xóa tất cả messages trong một conversation (không xóa conversation)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Lỗi khi clear messages: {str(e)}")
            return False