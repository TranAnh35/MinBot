from models.llm import LLM
from typing import List, Dict, Optional
from services.conversation.service import ConversationService
import faiss

class GeneratorService:
    
    def __init__(self) -> None:

        self.llm = LLM()
        self.conversation_service = ConversationService()
        self.quick_responses = {
            "hello": "Xin chào! Tôi có thể giúp gì cho bạn?",
            "hi": "Chào bạn! Tôi có thể hỗ trợ gì cho bạn hôm nay?",
            "xin chào": "Chào bạn! Tôi là ChatBot, tôi có thể giúp gì cho bạn?",
            "chào": "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?",
            "cảm ơn": "Không có gì, rất vui được giúp bạn!",
            "thank you": "Không có gì! Rất vui được giúp bạn.",
            "thanks": "Không có gì, rất vui được giúp bạn!"
        }

    async def generate_content(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        rag_response: Optional[str] = None,
        web_response: Optional[str] = None,
        file_response: Optional[str] = None
    ) -> str:
        """Tạo nội dung dựa trên prompt và các ngữ cảnh bổ sung."""
        prompt_lower = prompt.lower().strip()
        if (
            prompt_lower in self.quick_responses
            and not rag_response and not web_response and not file_response
        ):
            response = self.quick_responses[prompt_lower]
            if conversation_id:
                self.conversation_service.add_message(conversation_id, "user", prompt)
                self.conversation_service.add_message(conversation_id, "assistant", response)
            return response
        
        conversation_history = None
        if conversation_id:
            conversation_history = self.conversation_service.format_conversation_for_context(conversation_id)
        
        has_contextual_info = any(
            x is not None and len(str(x).strip()) > 0
            for x in [rag_response, web_response, file_response]
        )
        
        response = await self.llm.generateContent(
            prompt,
            rag_response if has_contextual_info else None,
            web_response if has_contextual_info else None,
            file_response if has_contextual_info else None,
            conversation_history
        )
        
        if conversation_id:
            self.conversation_service.add_message(conversation_id, "user", prompt)
            self.conversation_service.add_message(conversation_id, "assistant", response)
        
        return response
    
    async def merge_context(self, web_results: List[List[Dict]]) -> str:
        """Hợp nhất kết quả tìm kiếm web thành một văn bản thống nhất."""
        return await self.llm.merge_context(web_results)

    def create_vector_index(self) -> None:
        """Tạo chỉ số vector sử dụng thuật toán HNSW.
        
        Phương thức này khởi tạo một chỉ số vector sử dụng thuật toán HNSW (Hierarchical
        Navigable Small World) thay vì thuật toán FlatL2 để tăng hiệu suất tìm kiếm.
        """

        vector_size = self.llm.get_sentence_embedding_dimension()
        self.index = faiss.IndexHNSWFlat(vector_size, 32)