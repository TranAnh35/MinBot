from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.app_manager import app_manager
from config.app_config import AppConfig

router = APIRouter()

@router.get("/status", response_model=Dict[str, Any])
async def get_system_status():
    """Lấy trạng thái tổng quan của hệ thống."""
    try:
        health = await app_manager.health_check()
        system_info = app_manager.get_system_info()
        
        return {
            "status": "success",
            "system": system_info,
            "health": health,
            "timestamp": "now"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy trạng thái: {str(e)}")

@router.get("/services", response_model=Dict[str, Any])
async def get_services_info():
    """Lấy thông tin về tất cả services."""
    try:
        services = app_manager.get_all_services()
        services_info = {}
        
        for name, service in services.items():
            services_info[name] = {
                "type": type(service).__name__,
                "module": type(service).__module__,
                "available": True
            }
        
        return {
            "services": services_info,
            "total_services": len(services)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thông tin services: {str(e)}")

@router.get("/config", response_model=Dict[str, Any])
async def get_system_config():
    """Lấy cấu hình hệ thống (ẩn thông tin nhạy cảm)."""
    try:
        config = AppConfig()
        config_data = config.get_all_config()
        
        # Ẩn thông tin nhạy cảm
        sensitive_keys = ['GOOGLE_API_KEY', 'GOOGLE_SEARCH_API_KEY']
        for key in sensitive_keys:
            if key in config_data and config_data[key]:
                config_data[key] = "***HIDDEN***"
        
        return {
            "config": config_data,
            "validation": config.validate_config(),
            "config_sections": {
                "database": config.get_database_config(),
                "rag": config.get_rag_config(),
                "llm": config.get_llm_config(),
                "server": config.get_server_config()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy cấu hình: {str(e)}")

@router.post("/restart", response_model=Dict[str, str])
async def restart_system():
    """Khởi động lại hệ thống."""
    try:
        # Shutdown tất cả services
        await app_manager.shutdown()
        
        # Khởi tạo lại
        success = await app_manager.initialize()
        
        if success:
            return {"message": "Hệ thống đã được khởi động lại thành công"}
        else:
            raise HTTPException(status_code=500, detail="Khởi động lại thất bại")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi khởi động lại: {str(e)}")

@router.post("/validate-config", response_model=Dict[str, Any])
async def validate_system_config():
    """Kiểm tra tính hợp lệ của cấu hình."""
    try:
        config = AppConfig()
        validation = config.validate_config()
        
        return {
            "validation": validation,
            "config_summary": {
                "database_path": config.DATABASE_PATH,
                "upload_dir": config.UPLOAD_DIR,
                "api_key_configured": bool(config.GOOGLE_API_KEY),
                "search_configured": bool(config.GOOGLE_SEARCH_API_KEY and config.GOOGLE_SEARCH_ID)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi validate config: {str(e)}")

@router.get("/logs", response_model=Dict[str, Any])
async def get_system_logs():
    """Lấy log gần đây của hệ thống."""
    try:
        import os
        config = AppConfig()
        log_file = config.LOG_FILE
        
        if not os.path.exists(log_file):
            return {"logs": [], "message": "Log file không tồn tại"}
        
        # Đọc 50 dòng cuối của log file
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_logs = lines[-50:] if len(lines) > 50 else lines
        
        return {
            "logs": [line.strip() for line in recent_logs],
            "total_lines": len(lines),
            "showing_recent": len(recent_logs),
            "log_file": log_file
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc logs: {str(e)}")

@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics():
    """Lấy metrics hiệu suất hệ thống."""
    try:
        import psutil
        import os
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application metrics
        process = psutil.Process(os.getpid())
        app_memory = process.memory_info()
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_percent": memory.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_percent": round((disk.used / disk.total) * 100, 2)
            },
            "application": {
                "memory_rss_mb": round(app_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(app_memory.vms / (1024**2), 2),
                "pid": os.getpid(),
                "services_count": len(app_manager.get_all_services())
            }
        }
    except ImportError:
        return {"error": "psutil not available for performance metrics"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy performance metrics: {str(e)}") 