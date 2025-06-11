import os
import json
from typing import List, Dict, Optional
from datetime import datetime

class Conversation:
    
    def __init__(self):
        self.storage_dir = "storage/conversations"
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def create_conversation(self, user_id: str) -> str:
        """Tạo một hội thoại mới cho người dùng được chỉ định."""
        conversation_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        conversation_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "title": "Cuộc trò chuyện mới",  
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self._save_conversation(conversation_id, conversation_data)
        return conversation_id
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Thêm một tin nhắn vào hội thoại được chỉ định."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.now().isoformat()
        
        if conversation.get("title") == "Cuộc trò chuyện mới" and role == "user" and len(conversation["messages"]) <= 2:
            conversation["title"] = content[:30] + ("..." if len(content) > 30 else "")
        
        self._save_conversation(conversation_id, conversation)
        return True
    
    def rename_conversation(self, conversation_id: str, title: str) -> bool:
        """Đổi tên một hội thoại hiện có."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation["title"] = title
        conversation["updated_at"] = datetime.now().isoformat()
        
        self._save_conversation(conversation_id, conversation)
        return True
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Lấy thông tin hội thoại theo ID."""
        return self._load_conversation(conversation_id)
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Lấy lịch sử tin nhắn của một hội thoại."""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return []
        
        messages = conversation["messages"]
        if limit > 0:
            messages = messages[-limit:]
            
        return messages
    
    def list_conversations(self, user_id: str) -> List[Dict]:
        """Liệt kê tất cả hội thoại của một người dùng cụ thể."""
        conversations = []
        
        if not os.path.exists(self.storage_dir):
            return conversations
            
        for filename in os.listdir(self.storage_dir):
            if filename.startswith(f"{user_id}_") and filename.endswith(".json"):
                file_path = os.path.join(self.storage_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    conversation = json.load(f)
                    if conversation["messages"]:
                        last_message = conversation["messages"][-1]["content"]
                        conversation["preview"] = last_message[:50] + "..." if len(last_message) > 50 else last_message
                    else:
                        conversation["preview"] = "Empty conversation"
                    conversations.append(conversation)
        
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Xóa một hội thoại theo ID."""
        file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    def _save_conversation(self, conversation_id: str, data: Dict) -> None:
        """Lưu dữ liệu hội thoại vào file JSON."""
        file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Tải dữ liệu hội thoại từ file JSON."""
        file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)