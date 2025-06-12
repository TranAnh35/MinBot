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
            "xin chào": "Chào bạn! Tôi là MinBot, tôi có thể giúp gì cho bạn?",
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
        try:
            prompt_lower = prompt.lower().strip()
            if (
                prompt_lower in self.quick_responses
                and not rag_response and not web_response and not file_response
            ):
                response = self.quick_responses[prompt_lower]
                # Lưu message vào conversation nếu có, nhưng không gây lỗi nếu thất bại
                if conversation_id:
                    try:
                        # Sử dụng add_message_with_validation thay vì add_message trực tiếp
                        self.conversation_service.add_message_with_validation(conversation_id, "user", prompt)
                        self.conversation_service.add_message_with_validation(conversation_id, "assistant", response)
                    except Exception as e:
                        print(f"Warning: Không thể lưu quick response vào conversation: {str(e)}")
                return response
            
            conversation_history = None
            if conversation_id:
                try:
                    # Kiểm tra tồn tại của conversation trước khi lấy lịch sử
                    conversation = self.conversation_service.get_conversation(conversation_id)
                    if conversation:
                        conversation_history = self.conversation_service.format_conversation_for_context(conversation_id)
                    else:
                        print(f"Warning: Conversation {conversation_id} không tồn tại")
                except Exception as e:
                    print(f"Warning: Không thể lấy lịch sử hội thoại: {str(e)}")
                    # Xử lý mềm: tiếp tục với conversation_history = None
            
            has_contextual_info = any(
                x is not None and len(str(x).strip()) > 0
                for x in [rag_response, web_response, file_response]
            )
            
            response = await self.llm.generateContent(
                prompt,
                conversation_history,
                rag_response if has_contextual_info else None,
                web_response if has_contextual_info else None, 
                file_response if has_contextual_info else None
            )
            
            # Lưu message vào conversation nếu có, nhưng không gây lỗi nếu thất bại
            if conversation_id:
                try:
                    # Sử dụng add_message_with_validation thay vì add_message
                    user_result = self.conversation_service.add_message_with_validation(conversation_id, "user", prompt)
                    if not user_result.get("success"):
                        print(f"Warning: Không thể lưu user message: {user_result.get('error')}")
                    
                    assistant_result = self.conversation_service.add_message_with_validation(conversation_id, "assistant", response)
                    if not assistant_result.get("success"):
                        print(f"Warning: Không thể lưu assistant message: {assistant_result.get('error')}")
                except Exception as e:
                    print(f"Warning: Không thể lưu message vào conversation: {str(e)}")
            
            return response
        except Exception as e:
            print(f"Error in generate_content: {str(e)}")
            # Trả về tin nhắn lỗi để không làm gián đoạn UX
            return "Xin lỗi, đã xảy ra lỗi khi tạo nội dung. Vui lòng thử lại sau."
    async def merge_context(self, web_results) -> str:
        """Hợp nhất kết quả tìm kiếm web thành một văn bản thống nhất."""
        return await self.llm.merge_context(web_results)
        
    async def merge_context_from_search(self, search_results) -> str:
        """Tổng hợp kết quả tìm kiếm thành ngữ cảnh có cấu trúc."""
        if not search_results:
            return ""
        return await self.llm.merge_context_from_search(search_results)

    def create_vector_index(self) -> None:
        """Tạo chỉ số vector sử dụng thuật toán HNSW.
        
        Phương thức này khởi tạo một chỉ số vector sử dụng thuật toán HNSW (Hierarchical
        Navigable Small World) thay vì thuật toán FlatL2 để tăng hiệu suất tìm kiếm.
        """

        vector_size = self.llm.get_sentence_embedding_dimension()
        self.index = faiss.IndexHNSWFlat(vector_size, 32)