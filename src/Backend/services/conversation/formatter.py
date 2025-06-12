from typing import List, Dict

class ConversationFormatter:
    
    @staticmethod
    def format(messages: List[Dict], max_messages: int = 20) -> str:
        """Định dạng lịch sử hội thoại thành chuỗi context.
        
        Args:
            messages: Danh sách các tin nhắn trong lịch sử
            max_messages: Số lượng tin nhắn tối đa để giữ toàn bộ nội dung
            
        Returns:
            Chuỗi lịch sử hội thoại đã được định dạng
        """
        if not messages:
            return ""
            
        # Sắp xếp tin nhắn theo thứ tự thời gian (cũ nhất lên đầu)
        sorted_messages = sorted(messages, key=lambda x: x.get("timestamp", ""))
        
        # Giới hạn số lượng tin nhắn để đưa vào context
        recent_messages = sorted_messages[-max_messages:] if len(sorted_messages) > max_messages else sorted_messages
        
        formatted_history = "=== Lịch sử hội thoại (từ cũ đến mới) ===\n"
        
        # Nếu đã cắt bớt tin nhắn, thêm thông báo
        if len(sorted_messages) > max_messages:
            formatted_history += f"(Đã bỏ qua {len(sorted_messages) - max_messages} tin nhắn đầu tiên)\n\n"
        
        for idx, message in enumerate(recent_messages):
            role = message.get("role", "unknown")
            role_name = "User" if role == "user" else "Assistant" if role == "assistant" else "System"
            content = message.get("content", "")
            
            formatted_history += f"{role_name}: {content}\n\n"
            
        return formatted_history