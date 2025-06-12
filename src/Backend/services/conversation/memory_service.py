from typing import List, Dict, Optional, Any, Tuple
from models.memory import ConversationMemory
import re


class MemoryService:
    """Service để trích xuất và quản lý thông tin quan trọng từ hội thoại.
    
    Service này chịu trách nhiệm:
    1. Trích xuất entities và facts từ tin nhắn người dùng
    2. Lưu trữ thông tin này vào conversation memory
    3. Cung cấp thông tin từ memory để sử dụng trong các phản hồi
    """
    
    def __init__(self) -> None:
        """Khởi tạo MemoryService với ConversationMemory."""
        self.memory = ConversationMemory()
        
        # Định nghĩa các mẫu để trích xuất thông tin
        self.extraction_patterns = {
            "name": [
                r"(?:tên tôi là|tôi là|tôi tên là|gọi tôi là|mình là|mình tên là)\s+([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\s]+)(?:\.|,|\s|$)",
                r"(?:my name is|i am|i'm|call me)\s+([A-Za-z][A-Za-z\s]+)(?:\.|,|\s|$)"
            ],
            "age": [
                r"(?:tôi|mình|tao|ta)(?:\s+năm nay|\s+hiện)?\s+(\d+)\s+tuổi",
                r"(?:tôi|mình|tao|ta)\s+(\d+)\s+tuổi",
                r"(?:i am|i'm)\s+(\d+)\s+years?\s+old"
            ],
            "location": [
                r"(?:tôi|mình)(?:\s+đang)?\s+(?:sống|ở|làm việc|sinh sống|làm|học|làm việc)(?:\s+tại|\s+ở)?\s+([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\s]+)(?:\.|,|\s|$)",
                r"(?:i live|i work|i study|i am)(?:\s+in|\s+at)?\s+([A-Za-z][A-Za-z\s]+)(?:\.|,|\s|$)"
            ],
            "job": [
                r"(?:tôi|mình)(?:\s+là|\s+làm)?\s+(?:nghề|việc)?\s+([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\s]+)(?:\.|,|\s|$)",
                r"(?:i work as|i am an?|i'm an?)?\s+([A-Za-z][A-Za-z\s]+)(?:\.|,|\s|$)"
            ],
            "preference": [
                r"(?:tôi|mình)(?:\s+rất)?\s+(?:thích|yêu)(?:\s+về)?(?:\s+nhất)?\s+([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\s]+)(?:\.|,|\s|$)",
                r"(?:i like|i love|i prefer|i enjoy)(?:\s+to)?\s+([A-Za-z][A-Za-z\s]+)(?:\.|,|\s|$)"
            ]
        }
    
    def extract_entities_from_message(self, message: str) -> Dict[str, Tuple[str, float]]:
        """Trích xuất thông tin entities từ tin nhắn người dùng.
        
        Args:
            message: Nội dung tin nhắn cần trích xuất
            
        Returns:
            Dict chứa các entities đã trích xuất và độ tin cậy
        """
        extracted_entities = {}
        
        for entity_type, patterns in self.extraction_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, message.lower())
                for match in matches:
                    if len(match.groups()) > 0:
                        entity_value = match.group(1).strip()
                        if entity_value:
                            # Độ tin cậy mặc định là 0.8
                            confidence = 0.8
                            
                            # Tăng độ tin cậy nếu có các từ khóa mạnh mẽ
                            if "tên tôi là" in message.lower() or "my name is" in message.lower():
                                if entity_type == "name":
                                    confidence = 0.95
                            
                            extracted_entities[entity_type] = (entity_value, confidence)
                            break
        
        return extracted_entities
    
    def extract_and_save_from_message(self, conversation_id: str, message: str) -> Dict[str, str]:
        """Trích xuất và lưu entities từ tin nhắn người dùng.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            message: Nội dung tin nhắn
            
        Returns:
            Dict chứa các entities đã lưu thành công
        """
        extracted_entities = self.extract_entities_from_message(message)
        saved_entities = {}
        
        for entity_type, (entity_value, confidence) in extracted_entities.items():
            if self.memory.save_entity(conversation_id, entity_type, entity_value, confidence):
                saved_entities[entity_type] = entity_value
        
        return saved_entities
    
    def format_memory_for_context(self, conversation_id: str) -> str:
        """Định dạng thông tin memory để bổ sung vào context cho LLM.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            
        Returns:
            Chuỗi chứa thông tin memory đã định dạng
        """
        entities = self.memory.get_entities(conversation_id)
        facts = self.memory.get_facts(conversation_id)
        
        if not entities and not facts:
            return ""
        
        memory_context = "=== Thông tin đã ghi nhớ ===\n"
        
        # Thêm thông tin về entities
        if entities:
            for entity in entities:
                entity_type = entity["entity_type"]
                entity_value = entity["entity_value"]
                
                if entity_type == "name":
                    memory_context += f"- Tên người dùng: {entity_value}\n"
                elif entity_type == "age":
                    memory_context += f"- Tuổi người dùng: {entity_value}\n"
                elif entity_type == "location":
                    memory_context += f"- Địa điểm: {entity_value}\n"
                elif entity_type == "job":
                    memory_context += f"- Nghề nghiệp: {entity_value}\n"
                elif entity_type == "preference":
                    memory_context += f"- Sở thích: {entity_value}\n"
                else:
                    memory_context += f"- {entity_type.capitalize()}: {entity_value}\n"
        
        # Thêm thông tin về facts
        if facts:
            memory_context += "\nCác thông tin khác:\n"
            for fact in facts:
                memory_context += f"- {fact['fact']}\n"
        
        memory_context += "\n"
        return memory_context
    
    def get_entity_value(self, conversation_id: str, entity_type: str) -> Optional[str]:
        """Lấy giá trị của một entity cụ thể trong memory.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            entity_type: Loại entity cần lấy
            
        Returns:
            Giá trị của entity hoặc None nếu không có
        """
        return self.memory.get_entity_value(conversation_id, entity_type)
    
    def infer_user_name(self, conversation_id: str) -> Optional[str]:
        """Suy luận tên người dùng từ memory.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            
        Returns:
            Tên người dùng hoặc None nếu không có
        """
        return self.get_entity_value(conversation_id, "name")
    
    def clear_conversation_memory(self, conversation_id: str) -> bool:
        """Xóa toàn bộ memory của một cuộc hội thoại.
        
        Args:
            conversation_id: ID của cuộc hội thoại
            
        Returns:
            True nếu xóa thành công, False nếu có lỗi
        """
        return self.memory.clear_conversation_memory(conversation_id)
