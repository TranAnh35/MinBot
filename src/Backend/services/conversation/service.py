from typing import List, Dict, Optional, Any
from services.conversation.formatter import ConversationFormatter
from services.conversation.database_manager import ConversationDatabaseManager
from datetime import datetime


class ConversationService:
    
    def __init__(self) -> None:
        """Khởi tạo dịch vụ hội thoại với ConversationDatabaseManager."""
        self.db_manager = ConversationDatabaseManager()
    
    def create_conversation(self, user_id: str) -> str:
        """Tạo một hội thoại mới cho người dùng."""
        conversation_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if self.db_manager.create_conversation(conversation_id, user_id):
            return conversation_id
        else:
            conversation_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            if self.db_manager.create_conversation(conversation_id, user_id):
                return conversation_id
            else:
                raise Exception("Không thể tạo conversation ID duy nhất")
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Thêm một tin nhắn vào hội thoại."""
        success = self.db_manager.add_message(conversation_id, role, content)
        
        if success and role == "user":
            self.db_manager.auto_update_conversation_title(conversation_id, content)
        
        return success
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết của một hội thoại."""
        return self.db_manager.get_conversation(conversation_id)
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy lịch sử tin nhắn của một hội thoại."""
        return self.db_manager.get_conversation_history(conversation_id, limit)
    
    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Liệt kê tất cả hội thoại của một người dùng."""
        return self.db_manager.list_conversations(user_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Xóa một hội thoại."""
        return self.db_manager.delete_conversation(conversation_id)
    
    def rename_conversation(self, conversation_id: str, title: str) -> bool:
        """Đổi tên một hội thoại."""
        return self.db_manager.rename_conversation(conversation_id, title)
    
    def format_conversation_for_context(self, conversation_id: str, max_messages: int = 5) -> str:
        """Định dạng lịch sử hội thoại để sử dụng làm ngữ cảnh cho mô hình ngôn ngữ.
        Tối ưu hóa lịch sử hội thoại bằng cách giảm kích thước để phù hợp với giới hạn token."""

        messages = self.get_conversation_history(conversation_id, max_messages)
        return ConversationFormatter.format(messages, max_messages)
    
    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """Lấy thống kê conversations của user."""
        return self.db_manager.get_conversation_stats(user_id)
    
    def migrate_from_json_files(self, storage_dir: str = "storage/conversations") -> Dict[str, Any]:
        """Migration utility để chuyển dữ liệu từ JSON files sang database."""
        import os
        import json
        
        if not os.path.exists(storage_dir):
            return {
                "status": "error",
                "message": "Thư mục storage không tồn tại",
                "migrated": 0,
                "errors": 0
            }
        
        migrated_count = 0
        error_count = 0
        errors = []
        
        try:
            for filename in os.listdir(storage_dir):
                if not filename.endswith('.json'):
                    continue
                    
                file_path = os.path.join(storage_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        conversation_data = json.load(f)
                    
                    conversation_id = conversation_data.get('conversation_id')
                    user_id = conversation_data.get('user_id')
                    title = conversation_data.get('title', 'Cuộc trò chuyện mới')
                    messages = conversation_data.get('messages', [])
                    
                    if not conversation_id or not user_id:
                        error_count += 1
                        errors.append(f"File {filename}: Thiếu conversation_id hoặc user_id")
                        continue
                    
                    if self.db_manager.create_conversation(conversation_id, user_id):
                        if title != 'Cuộc trò chuyện mới':
                            self.db_manager.rename_conversation(conversation_id, title)
                        
                        for message in messages:
                            role = message.get('role')
                            content = message.get('content')
                            if role and content:
                                self.db_manager.add_message(conversation_id, role, content)
                        
                        migrated_count += 1
                        
                        backup_path = file_path + '.migrated'
                        os.rename(file_path, backup_path)
                        
                    else:
                        error_count += 1
                        errors.append(f"File {filename}: Không thể tạo conversation trong database")
                        
                except Exception as e:
                    error_count += 1
                    errors.append(f"File {filename}: {str(e)}")
                    
            return {
                "status": "success",
                "message": f"Migration hoàn thành: {migrated_count} conversations đã được migrate",
                "migrated": migrated_count,
                "errors": error_count,
                "error_details": errors[:10]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Lỗi trong quá trình migration: {str(e)}",
                "migrated": migrated_count,
                "errors": error_count
            }