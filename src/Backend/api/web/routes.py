from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.web.service import WebSearchService
from .schemas import WebSearchResponse

router = APIRouter()
web_search = WebSearchService()

@router.get("/search", response_model=WebSearchResponse)
async def search(query: str):
    """Thực hiện tìm kiếm trên công cụ tìm kiếm và trả về kết quả."""
    try:
        result = await web_search.perform_search(query)
        
        if isinstance(result, dict) and 'results' in result:
            return WebSearchResponse(
                results=result['results'],
                query_info=result.get('query_info'),
                total_results=result.get('total_results', 0),
                status=result.get('status', 'success'),
                error=result.get('error')
            )
        else:
            return WebSearchResponse(
                results=[],
                total_results=0,
                status='error',
                error='Invalid response format'
            )
    except Exception as e:
        return WebSearchResponse(
            results=[],
            total_results=0,
            status='error',
            error=str(e)
        )

@router.post("/page-content", response_model=Dict[str, Any])
async def page_content(url: str):
    """Lấy nội dung chính của một trang web từ URL được cung cấp."""
    try:
        return web_search.get_page_content(url)
    except Exception as e:
        return {
            "error": f"Lỗi khi lấy nội dung trang: {str(e)}",
            "url": url,
            "title": "",
            "content": ""
        }