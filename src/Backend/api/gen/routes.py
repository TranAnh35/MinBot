from fastapi import APIRouter, HTTPException
from services.llm.generator import GeneratorService
from services.conversation.service import ConversationService
from typing import Dict, Optional
from .schemas import WebResults

router = APIRouter()
gen_service = GeneratorService()
conversation_service = ConversationService()

@router.get("/gen_content", response_model=Dict[str, str])
async def generate_content(
    prompt: str, 
    conversation_id: Optional[str] = None, 
    rag_response: Optional[str] = None, 
    web_response: Optional[str] = None, 
    file_response: Optional[str] = None
) -> Dict[str, str]:
    """Tạo nội dung dựa trên prompt và các ngữ cảnh bổ sung."""
    try:
        conversation_history = ""
        
        # Kiểm tra tính hợp lệ của conversation_id
        if conversation_id:
            try:
                # Kiểm tra xem conversation có tồn tại không
                conversation = conversation_service.get_conversation(conversation_id)
                if not conversation:
                    print(f"Warning: Conversation {conversation_id} không tồn tại")
                else:
                    # Tăng số lượng tin nhắn lấy về từ 10 lên 20
                    conversation_history = conversation_service.format_conversation_for_context(conversation_id, max_messages=20)
            except Exception as conv_error:
                print(f"Warning: Lỗi khi lấy lịch sử hội thoại: {str(conv_error)}")
                # Nếu lỗi, vẫn tiếp tục nhưng không có lịch sử
                conversation_history = ""
        
        # Gọi service để tạo nội dung
        content = await gen_service.generate_content(
            prompt,
            conversation_id,  # Vẫn truyền conversation_id, bất kể có lỗi không
            rag_response,
            web_response,
            file_response
        )

        # Lưu phản hồi vào conversation nếu có
        if conversation_id:
            try:
                # Sử dụng add_message_with_validation để tạo conversation nếu cần
                result = conversation_service.add_message_with_validation(conversation_id, "assistant", content)
                if not result.get("success"):
                    print(f"Warning: Không thể lưu phản hồi: {result.get('error')}")
            except Exception as add_msg_error:
                print(f"Warning: Lỗi khi lưu phản hồi: {str(add_msg_error)}")
                # Tiếp tục trả về nội dung dù không lưu được

        return {"content": content}
    except Exception as e:
        print(f"Error in gen_content: {str(e)}")
        # Trả về lỗi rõ ràng hơn để debug
        error_message = f"Error generating content: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)

@router.post("/merge_context", response_model=Dict[str, str])
async def merge_context(web_results: WebResults) -> Dict[str, str]:
    """Hợp nhất và xử lý ngữ cảnh từ nhiều kết quả tìm kiếm web."""
    try:
        results_data = web_results.results
        
        if isinstance(results_data, dict):
            if 'results' in results_data:
                search_results = results_data['results']
            else:
                search_results = []
        elif isinstance(results_data, list):
            search_results = results_data
        else:
            search_results = []
        
        if not search_results:
            return {"content": "Không có kết quả tìm kiếm để xử lý."}
        
        content = await gen_service.merge_context_from_search(search_results)
        return {"content": content}
        
    except Exception as e:
        print(f"Error in merge_context: {str(e)}")
        return {"content": f"Lỗi khi xử lý kết quả tìm kiếm: {str(e)}"} 