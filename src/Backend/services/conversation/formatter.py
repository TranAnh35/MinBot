from typing import List, Dict

class ConversationFormatter:
    
    @staticmethod
    def format(messages: List[Dict], max_messages: int = 5) -> str:
        """Định dạng lịch sử hội thoại thành chuỗi context."""
        if not messages:
            return ""
        if len(messages) > 3:
            for i in range(len(messages) - 3):
                if len(messages[i]["content"]) > 100:
                    messages[i]["content"] = messages[i]["content"][:100] + "..."
        formatted_history = ""
        for message in messages:
            role_prefix = "U" if message["role"] == "user" else "A"
            formatted_history += f"{role_prefix}: {message['content']}\n"
        return formatted_history 