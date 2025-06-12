import google.generativeai as genai
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
load_dotenv()

class LLM:
    
    def __init__(self):
        try:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model = genai.GenerativeModel("gemini-2.0-flash-lite")
        except AttributeError:
            # Fallback if the API changes
            print("Warning: GenerativeAI API initialization failed, using compatible methods")
        
        self.system_prompt = """Bạn là ChatBot, một trợ lý AI thông minh được phát triển để hỗ trợ người dùng một cách toàn diện và chuyên nghiệp.

            Nguyên tắc hoạt động:
            1. Luôn cung cấp thông tin chính xác, đáng tin cậy và cập nhật.
            2. Trả lời tự nhiên, thân thiện và dễ hiểu.
            3. Không đưa ra thông tin sai lệch hoặc có hại.
            4. Tôn trọng quyền riêng tư của người dùng.
            5. Thừa nhận giới hạn kiến thức khi cần thiết.

            Khả năng:
            - Phân tích và trả lời các câu hỏi về nhiều lĩnh vực khác nhau
            - Tổng hợp thông tin từ nhiều nguồn (tài liệu, web, file đính kèm)
            - Hỗ trợ nhiều ngôn ngữ, đặc biệt là tiếng Việt
            - Điều chỉnh giọng điệu phù hợp với ngữ cảnh (chính thức, thân thiện, hỗ trợ kỹ thuật)

            Khi cung cấp câu trả lời:
            - Ưu tiên sử dụng thông tin từ nguồn đáng tin cậy (tài liệu RAG, web, file đính kèm)
            - Cấu trúc câu trả lời rõ ràng, dễ đọc
            - Khi thích hợp, đề xuất các bước tiếp theo hoặc tài nguyên bổ sung
            - Nếu không chắc chắn, nêu rõ những giới hạn và cung cấp câu trả lời tốt nhất có thể

            Bạn được thiết kế để giúp đỡ trong các lĩnh vực từ giáo dục, công việc đến giải trí và đời sống hàng ngày, nhưng luôn tuân thủ các nguyên tắc đạo đức và pháp luật."""

    async def generateContent(self, prompt: str, conversation_history: Optional[str] = None, 
                             rag_response: Optional[str] = None, web_response: Optional[str] = None, 
                             file_response: Optional[str] = None) -> str:
        """Tạo nội dung dựa trên prompt và ngữ cảnh được cung cấp.
        
        Kết hợp prompt hệ thống, lịch sử hội thoại và bất kỳ ngữ cảnh nào được cung cấp
        (RAG, web, file) để tạo ra phản hồi phù hợp và mạch lạc.
        
        Args:
            prompt: Câu hỏi của người dùng
            conversation_history: Lịch sử hội thoại đã được định dạng
            rag_response: Thông tin từ RAG
            web_response: Thông tin từ tìm kiếm web
            file_response: Thông tin từ file đính kèm
            
        Returns:
            Nội dung phản hồi được tạo ra
        """
        try:
            needs_analysis = self.should_analyze_prompt(prompt)
            analysis_response = ""
            if needs_analysis:
                analysis_response = await self.analyze_communication_context(prompt)
            
            # Bắt đầu với system prompt
            combined_prompt = f"System: {self.system_prompt}\n\n"

            # Ưu tiên đưa lịch sử hội thoại vào để cung cấp ngữ cảnh
            if conversation_history is not None and len(conversation_history.strip()) > 0:
                combined_prompt += f"{conversation_history}\n\n"
                combined_prompt += "Lưu ý: Hãy tham khảo lịch sử hội thoại và thông tin đã ghi nhớ ở trên để đảm bảo phản hồi của bạn cá nhân hóa và nhất quán với các trao đổi trước đó. Nếu có thông tin về tên, tuổi hoặc các thuộc tính cá nhân khác của người dùng, hãy sử dụng chúng khi thích hợp.\n\n"
            
            context_added = False
            
            # Thêm thông tin RAG nếu có
            if rag_response is not None and len(rag_response.strip()) > 0:
                combined_prompt += f"Thông tin RAG:\n{rag_response}\n\n"
                context_added = True
                
            # Thêm thông tin Web nếu có
            if web_response is not None and len(web_response.strip()) > 0:
                combined_prompt += f"Thông tin web:\n{web_response}\n\n"
                context_added = True

            # Thêm thông tin file nếu có
            if file_response is not None and len(file_response.strip()) > 0:
                combined_prompt += f"Thông tin file:\n{file_response}\n\n"
                context_added = True

            # Thêm câu hỏi người dùng
            combined_prompt += f"Câu hỏi: {prompt}\n\n"
            
            # Nếu có phân tích thì thêm vào
            if needs_analysis and analysis_response:
                combined_prompt += f"Phân tích: {analysis_response}\n\n"

            # Chỉ dẫn cuối cùng
            if context_added:
                combined_prompt += "Trả lời dựa trên thông tin cung cấp và kiến thức của bạn."
            else:
                combined_prompt += "Trả lời dựa trên kiến thức của bạn."
            
            # Gọi API để lấy phản hồi
            response = await self.model.generate_content_async(combined_prompt)
            return response.text

        except Exception as e:
            print(f"Lỗi khi tạo nội dung: {str(e)}")
            return "Xin lỗi, tôi không thể tạo nội dung lúc này."
    
    def should_analyze_prompt(self, prompt: str) -> bool:
        """Xác định xem prompt có cần phân tích chi tiết không.
        
        Sử dụng các heuristic như độ dài, dấu hỏi và từ khóa cụ thể
        để quyết định xem prompt có cần xử lý bổ sung không.
        """
        if len(prompt) < 10 or "?" not in prompt:
            return False
            
        analysis_keywords = ["tìm kiếm", "tìm", "web", "file", "tài liệu", 
                           "so sánh", "nghiên cứu", "phân tích", "giải thích"]
        for keyword in analysis_keywords:
            if keyword in prompt.lower():
                return True
                
        return False
    
    async def analyze_communication_context(self, prompt: str) -> str:
        """Phân tích ngữ cảnh giao tiếp của một prompt.
        
        Xác định thông tin bổ sung có thể cần thiết để phản hồi prompt,
        chẳng hạn như kết quả tìm kiếm web hoặc nội dung file.
        """
        try:
            combined_prompt = f"""Phân tích ngắn gọn câu hỏi: "{prompt}"
                                Cần thông tin web? (có/không)
                                Cần thông tin từ file? (có/không)
                                Trạng thái giao tiếp? (xã giao/nghiêm túc/vui vẻ/...)
                                Chỉ trả lời 3 dòng ngắn gọn."""
            
            response = await self.model.generate_content_async(combined_prompt)
            return response.text

        except Exception as e:
            print(f"Lỗi khi phân tích prompt: {str(e)}")
            return ""
    
    async def merge_context(self, web_results: List[Dict]) -> str:
        """Hợp nhất và loại bỏ trùng lặp kết quả tìm kiếm web thành ngữ cảnh mạch lạc.
        
        Xử lý nhiều kết quả tìm kiếm web, loại bỏ trùng lặp và định dạng
        thành một chuỗi dễ đọc cho mô hình ngôn ngữ.
        """
        seen_snippets = set()
        merged_context = ""

        for result in web_results:
            snippet = result.get("snippet", "").strip()
            if snippet and snippet not in seen_snippets:
                merged_context += f"- {snippet}\n"
                seen_snippets.add(snippet)

        if not merged_context:
            return "Không có thông tin hợp lệ để tổng hợp."

        prompt = f"""Tổng hợp ngắn gọn các thông tin sau thành một đoạn văn duy nhất:
                {merged_context}
                Viết lại đầy đủ, dễ hiểu nhưng không mất ý chính. Không đề cập nguồn gốc thông tin."""

        response = await self.model.generate_content_async(prompt)
        return response.text
        
    async def merge_context_from_search(self, search_results: List[Dict]) -> str:
        """Tổng hợp kết quả tìm kiếm thành ngữ cảnh có cấu trúc."""
        return await self.merge_context(search_results)
    
    def get_sentence_embedding_dimension(self) -> int:
        """Trả về kích thước của vector embedding cho câu."""
        return 768  # Kích thước embedding mặc định
