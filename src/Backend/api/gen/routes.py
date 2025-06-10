from fastapi import APIRouter, HTTPException
from services.llm.generator import GeneratorService
from typing import Dict, Optional, Any
from .schemas import WebResults, WebSearchResponse

router = APIRouter()
gen_service = GeneratorService()

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
        content = await gen_service.generate_content(
            prompt, 
            conversation_id, 
            rag_response, 
            web_response, 
            file_response
        )
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")

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
        
        content = await gen_service.merge_context(search_results)
        return {"content": content}
        
    except Exception as e:
        print(f"Error in merge_context: {str(e)}")
        return {"content": f"Lỗi khi xử lý kết quả tìm kiếm: {str(e)}"} 