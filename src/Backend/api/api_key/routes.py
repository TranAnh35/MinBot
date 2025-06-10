from fastapi import APIRouter, Body, HTTPException
from services.api_manager import ApiManager
from typing import Dict

router = APIRouter()
api_manager = ApiManager()

@router.get("/get_api_key", response_model=Dict[str, str])
async def get_api_key():
    """Lấy API key hiện tại.

    Returns:
        dict: Chứa API key hiện tại hoặc thông báo lỗi nếu chưa thiết lập.
    """
    return api_manager.get_api_key()

@router.post("/set_api_key", response_model=Dict[str, str])
async def set_api_key(api_key: str = Body(...)):
    """Thiết lập API key mới.

    Args:
        api_key (str): API key cần thiết lập.
    Returns:
        dict: Thông báo thành công hoặc lỗi nếu có.
    Raises:
        HTTPException: 500 nếu có lỗi server khi thiết lập API key.
    """
    try:
        api_manager.set_api_key(api_key)
        return {"message": "Đã thiết lập API key thành công"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate_api_key", response_model=Dict[str, bool])
async def validate_api_key(api_key: str = Body(...)):
    """Xác thực API key.

    Args:
        api_key (str): API key cần xác thực.
    Returns:
        dict: Trạng thái hợp lệ của API key.
    """
    is_valid = api_manager.is_api_key_valid(api_key)
    return {"valid": is_valid}