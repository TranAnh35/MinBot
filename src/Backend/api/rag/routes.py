from fastapi import APIRouter
from services.rag.rag import RAGService
from typing import Dict, Any

router = APIRouter()
rag_service = RAGService()

@router.get("/query", response_model=Dict[str, str])
async def rag_query(question: str):
    """Truy vấn hệ thống RAG với câu hỏi đầu vào. """
    response = await rag_service.query(question)
    return {"response": response}

@router.post("/sync-files", response_model=Dict[str, str])
async def sync_files():
    """Đồng bộ dữ liệu từ thư mục upload vào VectorDB. """
    updated = await rag_service.check_and_update_files()
    return {
        "message": "Đã đồng bộ dữ liệu thành công" if updated 
        else "Không có thay đổi nào được phát hiện"
    }

@router.post("/force-rebuild", response_model=Dict[str, Any])
async def force_rebuild_from_files():
    """Force rebuild toàn bộ database và index từ file upload (dùng khi database bị xóa)."""
    try:
        from utils.rag_file_utils import get_uploaded_files_info
        upload_info = get_uploaded_files_info(rag_service.upload_dir)
        
        if not upload_info:
            return {
                "status": "warning",
                "message": "Không có file nào trong thư mục upload để rebuild",
                "files_processed": 0
            }
        
        files_processed = 0
        for file_name in upload_info.keys():
            try:
                file_path = f"{rag_service.upload_dir}/{file_name}"
                await rag_service.vector_db.process_file(file_path)
                files_processed += 1
            except Exception as e:
                print(f"Lỗi khi xử lý file {file_name}: {str(e)}")
        
        if files_processed > 0:
            await rag_service._rebuild_index_from_database()
        
        return {
            "status": "success",
            "message": f"Đã rebuild thành công database từ {files_processed} file upload",
            "files_processed": files_processed,
            "total_files_found": len(upload_info)
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Lỗi khi rebuild database: {str(e)}",
            "files_processed": 0
        }

@router.post("/rebuild-index", response_model=Dict[str, str])
async def rebuild_index():
    """Xây dựng lại FAISS index từ dữ liệu trong database."""
    try:
        await rag_service._rebuild_index_from_database()
        return {"message": "Đã xây dựng lại FAISS index thành công"}
    except Exception as e:
        return {"message": f"Lỗi khi xây dựng lại index: {str(e)}"}

@router.get("/index-stats", response_model=Dict[str, Any])
async def get_index_statistics():
    """Lấy thống kê về FAISS index và hiệu suất."""
    try:
        stats = rag_service.get_index_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi khi lấy thống kê: {str(e)}"
        }

@router.post("/optimize-index", response_model=Dict[str, str])
async def optimize_index():
    """Tối ưu hóa FAISS index hiện tại."""
    try:
        if rag_service.index is None:
            return {"message": "Không có index để tối ưu hóa"}
        
        from utils.faiss_utils import optimize_search_params
        optimize_search_params(rag_service.index)
        
        return {"message": "Đã tối ưu hóa FAISS index thành công"}
    except Exception as e:
        return {"message": f"Lỗi khi tối ưu hóa index: {str(e)}"}

@router.get("/query-advanced", response_model=Dict[str, Any])
async def rag_query_advanced(question: str, k: int = 5, include_scores: bool = False):
    """Truy vấn RAG nâng cao với tùy chọn số lượng kết quả và điểm số."""
    try:
        response = await rag_service.query(question, k=k)
        result = {
            "response": response,
            "query_params": {
                "k": k,
                "include_scores": include_scores
            }
        }
        
        if include_scores and rag_service.index:
            # Thêm thông tin về search quality
            import numpy as np
            query_embedding = rag_service.model.encode([question])
            query_embedding = np.array(query_embedding, dtype='float32')
            
            search_k = min(k, rag_service.index.ntotal)
            D, I = rag_service.index.search(query_embedding, k=search_k)
            
            result["search_info"] = {
                "distances": D[0].tolist(),
                "indices": I[0].tolist(),
                "avg_distance": float(np.mean(D[0])),
                "min_distance": float(np.min(D[0])),
                "max_distance": float(np.max(D[0]))
            }
        
        return result
        
    except Exception as e:
        return {
            "response": f"Lỗi khi xử lý truy vấn: {str(e)}",
            "error": True
        }