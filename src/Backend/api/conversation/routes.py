from fastapi import APIRouter, HTTPException
from .schemas import ConversationCreate, MessageCreate, ConversationRename
from services.conversation.service import ConversationService
from services.vector_db.database_manager import DatabaseManager
from typing import List, Dict, Any

router = APIRouter()
conversation_service = ConversationService()

@router.post("/create", response_model=Dict[str, str])
async def create_conversation(request: ConversationCreate):
    """Tạo một hội thoại mới."""
    conversation_id = conversation_service.create_conversation(request.user_id)
    return {"conversation_id": conversation_id}

@router.post("/message", response_model=Dict[str, bool])
async def add_message(request: MessageCreate):
    """Thêm tin nhắn vào hội thoại."""
    success = conversation_service.add_message(
        request.conversation_id,
        request.role,
        request.content
    )
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return {"success": True}

@router.post("/rename", response_model=Dict[str, bool])
async def rename_conversation(request: ConversationRename):
    """Đổi tên hội thoại."""
    success = conversation_service.rename_conversation(
        request.conversation_id,
        request.title
    )
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return {"success": True}

@router.get("/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(conversation_id: str):
    """Lấy thông tin chi tiết của một hội thoại."""
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return conversation

@router.get("/{conversation_id}/history", response_model=Dict[str, List[Dict]])
async def get_conversation_history(conversation_id: str, limit: int = 10):
    """Lấy lịch sử tin nhắn của một hội thoại."""
    messages = conversation_service.get_conversation_history(conversation_id, limit)
    return {"messages": messages}

@router.get("/user/{user_id}", response_model=Dict[str, List[Dict]])
async def list_user_conversations(user_id: str):
    """Liệt kê tất cả hội thoại của một người dùng."""
    conversations = conversation_service.list_conversations(user_id)
    return {"conversations": conversations}

@router.delete("/{conversation_id}", response_model=Dict[str, bool])
async def delete_conversation(conversation_id: str):
    """Xóa một hội thoại."""
    success = conversation_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return {"success": True}

@router.get("/user/{user_id}/stats", response_model=Dict[str, Any])
async def get_user_conversation_stats(user_id: str):
    """Lấy thống kê conversations của user."""
    stats = conversation_service.get_conversation_stats(user_id)
    return {"stats": stats}

@router.post("/migrate-from-json", response_model=Dict[str, Any])
async def migrate_conversations_from_json():
    """Migration conversations từ JSON files sang database."""
    try:
        result = conversation_service.migrate_from_json_files()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi migration: {str(e)}")

@router.get("/database/status", response_model=Dict[str, Any])
async def get_database_status():
    """Kiểm tra trạng thái database và khả năng kết nối."""
    try:
        # Test connection bằng cách lấy stats của user test
        test_stats = conversation_service.get_conversation_stats("test_user")
        return {
            "status": test_stats,
            "message": "Database hoạt động bình thường",
            "database_type": "SQLite",
            "test_query_success": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi kết nối database: {str(e)}",
            "database_type": "SQLite",
            "test_query_success": False
        }

@router.get("/database/info", response_model=Dict[str, Any])
async def get_database_info():
    """Lấy thông tin chi tiết về database."""
    try:
        db_manager = DatabaseManager()
        db_info = db_manager.get_database_info()
        return {
            "status": "success",
            "database_info": db_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thông tin database: {str(e)}")