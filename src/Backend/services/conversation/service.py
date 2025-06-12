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
    
    def get_conversation_history(self, conversation_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Lấy lịch sử tin nhắn của một hội thoại với hỗ trợ pagination."""
        return self.db_manager.get_conversation_history(conversation_id, limit, offset)
    
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
    
    def get_formatted_conversation_history(self, conversation_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Lấy lịch sử conversation đã được format cho frontend với pagination."""
        try:
            raw_messages = self.db_manager.get_conversation_history(conversation_id, limit, offset)
            total_count = self.db_manager.count_conversation_messages(conversation_id)
            
            formatted_messages = [
                {
                    "id": f"{msg['role']}_{msg['timestamp']}_{offset + i}",
                    "content": msg["content"],
                    "sender": "user" if msg["role"] == "user" else "bot",
                    "timestamp": msg["timestamp"],
                    "sequence": offset + i + 1,
                }
                for i, msg in enumerate(raw_messages)
            ]
            
            return {
                "messages": formatted_messages,
                "has_more": total_count > offset + len(raw_messages),
                "total_count": total_count,
            }
        except Exception as e:
            print(f"Lỗi khi format conversation history: {str(e)}")
            return {"messages": [], "has_more": False, "total_count": 0}
    
    def add_message_with_validation(self, conversation_id: str, role: str, content: str, attachments: Optional[list] = None) -> Dict[str, Any]:
        """Thêm message với validation và trả về thông tin chi tiết."""
        try:
            if not all([conversation_id, role, content]):
                return {"success": False, "error": "Missing required fields"}

            if not self.db_manager.get_conversation(conversation_id):
                try:
                    # Tự động tạo conversation nếu không tồn tại, user_id được suy ra từ conversation_id
                    user_id = conversation_id.rsplit('_', 1)[0]
                    if not self.db_manager.create_conversation(conversation_id, user_id):
                        return {"success": False, "error": "Failed to auto-create conversation"}
                except IndexError:
                    return {"success": False, "error": "Invalid conversation_id format for auto-creation"}

            recent_messages = self.db_manager.get_recent_messages(conversation_id, 5)
            for msg in recent_messages:
                if msg["role"] == role and msg["content"] == content:
                    # Bỏ qua kiểm tra trùng lặp nếu có file đính kèm
                    if not attachments:
                        return {"success": True, "note": "Duplicate message detected", "message": msg}

            if self.db_manager.add_message(conversation_id, role, content, attachments):
                if role == "user":
                    self.db_manager.auto_update_conversation_title(conversation_id, content)
                
                new_message = self.db_manager.get_latest_message(conversation_id)
                return {"success": True, "message": new_message}
            
            return {"success": False, "error": "Failed to add message"}
        except Exception as e:
            print(f"Lỗi khi thêm message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Lấy tóm tắt conversation bao gồm thông tin cơ bản và message count."""
        try:
            conversation = self.db_manager.get_conversation(conversation_id)
            if not conversation:
                return {"error": "Conversation not found"}
            
            # Đếm số messages
            message_count = self.db_manager.count_conversation_messages(conversation_id)
            
            # Lấy message cuối cùng
            latest_message = self.db_manager.get_latest_message(conversation_id)
            
            return {
                "conversation_id": conversation["conversation_id"],
                "title": conversation["title"],
                "user_id": conversation["user_id"],
                "created_at": conversation["created_at"],
                "updated_at": conversation["updated_at"],
                "message_count": message_count,
                "latest_message": latest_message,
                "has_messages": message_count > 0
            }
            
        except Exception as e:
            print(f"Lỗi khi lấy conversation summary: {str(e)}")
            return {"error": str(e)}
    
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