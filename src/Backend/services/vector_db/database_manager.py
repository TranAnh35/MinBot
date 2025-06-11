import os
import sqlite3
import threading
from typing import Optional, Tuple, List
from contextlib import contextmanager


class DatabaseManager:
    """Quản lý các operations liên quan đến database SQLite."""
    
    def __init__(self, db_path: str = "vector_store.db") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        
    def init_db(self) -> None:
        """Khởi tạo cơ sở dữ liệu SQLite."""
        with self._lock:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    self._ensure_files_table(cursor)
                    self._ensure_chunks_table(cursor)
                    self._ensure_conversations_table(cursor)
                    self._ensure_messages_table(cursor)
                    self._ensure_indexes(cursor)
                    
                    self._migrate_legacy_documents_table(cursor)
                    
                    self._cleanup_legacy_tables(cursor)
                    
                    conn.commit()
                    print("Đã khởi tạo/cập nhật database thành công")
            except Exception as e:
                print(f"Lỗi khi khởi tạo database: {str(e)}")
                raise

    @contextmanager
    def get_connection(self):
        """Context manager để quản lý database connection."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _table_exists(self, cursor: sqlite3.Cursor, table_name: str) -> bool:
        """Kiểm tra xem table có tồn tại không."""
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None

    def _ensure_files_table(self, cursor: sqlite3.Cursor) -> None:
        """Đảm bảo table files tồn tại."""
        if not self._table_exists(cursor, 'files'):
            cursor.execute('''
                CREATE TABLE files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    size INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("Đã tạo table 'files'")

    def _ensure_chunks_table(self, cursor: sqlite3.Cursor) -> None:
        """Đảm bảo table chunks tồn tại."""
        if not self._table_exists(cursor, 'chunks'):
            cursor.execute('''
                CREATE TABLE chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files (id),
                    UNIQUE(file_id, chunk_index)
                )
            ''')
            print("Đã tạo table 'chunks'")

    def _ensure_conversations_table(self, cursor: sqlite3.Cursor) -> None:
        """Đảm bảo table conversations tồn tại."""
        if not self._table_exists(cursor, 'conversations'):
            cursor.execute('''
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("Đã tạo table 'conversations'")

    def _ensure_messages_table(self, cursor: sqlite3.Cursor) -> None:
        """Đảm bảo table messages tồn tại."""
        if not self._table_exists(cursor, 'messages'):
            cursor.execute('''
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
                )
            ''')
            print("Đã tạo table 'messages'")

    def _ensure_indexes(self, cursor: sqlite3.Cursor) -> None:
        """Đảm bảo tất cả indexes cần thiết tồn tại."""
        indexes = [
            ("idx_conversations_user_id", "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id)"),
            ("idx_conversations_updated_at", "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations (updated_at)"),
            ("idx_messages_conversation_id", "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id)"),
            ("idx_messages_timestamp", "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)")
        ]
        
        for index_name, create_sql in indexes:
            try:
                cursor.execute(create_sql)
            except Exception as e:
                print(f"Lỗi khi tạo index {index_name}: {e}")

    def _migrate_legacy_documents_table(self, cursor: sqlite3.Cursor) -> None:
        """Migrate dữ liệu từ table documents cũ (nếu tồn tại) sang files và chunks."""
        if not self._table_exists(cursor, 'documents'):
            return
            
        try:
            print("Phát hiện table 'documents' cũ, bắt đầu migration...")
            
            # Backup table cũ
            cursor.execute("CREATE TABLE IF NOT EXISTS documents_backup AS SELECT * FROM documents")
            
            # Migrate dữ liệu
            cursor.execute("""
                INSERT OR IGNORE INTO files (name, size, created_at, updated_at)
                SELECT DISTINCT source, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                FROM documents_backup
            """)
            
            cursor.execute("""
                INSERT OR IGNORE INTO chunks (file_id, content, chunk_index, created_at)
                SELECT DISTINCT f.id, d.text, d.chunk_index, CURRENT_TIMESTAMP
                FROM documents_backup d
                JOIN files f ON f.name = d.source
                WHERE NOT EXISTS (
                    SELECT 1 FROM chunks c 
                    WHERE c.file_id = f.id AND c.chunk_index = d.chunk_index
                )
            """)
            
            cursor.execute("DROP TABLE documents")
            cursor.execute("DROP TABLE documents_backup")
            
            print("Migration từ table 'documents' hoàn thành")
            
        except Exception as e:
            print(f"Lỗi khi migrate table documents: {str(e)}")
            cursor.execute("DROP TABLE IF EXISTS documents_backup")
            raise

    def _cleanup_legacy_tables(self, cursor: sqlite3.Cursor) -> None:
        """Xóa các table legacy không cần thiết."""
        if self._table_exists(cursor, 'version'):
            try:
                cursor.execute("DROP TABLE version")
                print("Đã xóa table 'version' cũ")
            except Exception as e:
                print(f"Lỗi khi xóa table version: {e}")

    def check_file_changed(
        self, 
        file_name: str, 
        content_size: int
    ) -> Tuple[bool, Optional[int]]:
        """Kiểm tra xem file đã thay đổi so với bản lưu trữ trong database chưa."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, size FROM files WHERE name = ?", (file_name,))
                result = cursor.fetchone()
                
                if not result:
                    return True, None  
                    
                file_id, old_size = result
                if old_size == content_size:
                    cursor.execute(
                        "UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                        (file_id,)
                    )
                    conn.commit()
                    return False, file_id
                    
                return True, file_id
        except Exception as e:
            print(f"Lỗi khi kiểm tra file {file_name}: {str(e)}")
            return True, None

    def update_file_metadata(self, file_name: str, content_size: int) -> int:
        """Cập nhật thông tin metadata của file trong database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO files (name, size, created_at, updated_at)
                    VALUES (?, ?, 
                        COALESCE((SELECT created_at FROM files WHERE name = ?), CURRENT_TIMESTAMP),
                        CURRENT_TIMESTAMP)
                """, (file_name, content_size, file_name))
                
                cursor.execute("SELECT id FROM files WHERE name = ?", (file_name,))
                result = cursor.fetchone()
                
                conn.commit()
                return result[0] if result else None
        except Exception as e:
            print(f"Lỗi khi cập nhật metadata file {file_name}: {str(e)}")
            raise

    def update_file_chunks(self, file_id: int, chunks: List[str]) -> None:
        """Cập nhật các chunks của file trong database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
            
            for chunk_index, chunk in enumerate(chunks):
                cursor.execute("""
                    INSERT INTO chunks (file_id, content, chunk_index, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (file_id, chunk, chunk_index))
            
            conn.commit()

    def delete_file_from_db(self, file_name: str) -> None:
        """Xóa dữ liệu của file khỏi database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("BEGIN TRANSACTION")
                
                cursor.execute("SELECT id FROM files WHERE name = ?", (file_name,))
                result = cursor.fetchone()
                
                if result:
                    file_id = result[0]
                    cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                
                conn.commit()
                print(f"Đã xóa dữ liệu của file {file_name} khỏi database")
                
            except Exception as e:
                conn.rollback()
                raise e

    def reset_db(self) -> None:
        """Xóa và tạo lại cơ sở dữ liệu từ đầu."""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print(f"Đã xóa database cũ: {self.db_path}")
            
            self.init_db()
            print("Đã tạo database mới thành công")
        except Exception as e:
            print(f"Lỗi khi reset database: {str(e)}")
            raise

    def get_database_info(self) -> dict:
        """Lấy thông tin về database và các tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                except Exception:
                    table_counts[table] = "Error"
            
            return {
                "database_path": self.db_path,
                "tables": tables,
                "table_counts": table_counts,
                "database_size": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            }

    def get_file_modification_times(self) -> dict:
        """Lấy thời gian modification của tất cả files từ database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, updated_at FROM files")
            
            file_mtimes = {}
            for row in cursor.fetchall():
                file_name, updated_at = row
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    file_mtimes[file_name] = dt.timestamp()
                except Exception:
                    file_mtimes[file_name] = 0.0
            
            return file_mtimes 