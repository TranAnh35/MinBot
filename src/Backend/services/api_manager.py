import os
from dotenv import load_dotenv, set_key
import requests
from typing import Optional

load_dotenv()

class ApiManager:
    
    def __init__(self) -> None:
        """Khởi tạo ApiManager và tải API key từ biến môi trường."""
        self.api_key = os.getenv("GOOGLE_API_KEY")

    def get_api_key(self) -> Optional[str]:
        """Lấy API key hiện tại."""
        return self.api_key

    def set_api_key(self, api_key: str) -> None:
        """Thiết lập API key mới."""
        self.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        set_key(".env", "GOOGLE_API_KEY", api_key)
        
    def is_api_key_valid(self, api_key: str) -> bool: 
        """Kiểm tra tính hợp lệ của API key bằng cách gửi yêu cầu thử nghiệm."""
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
        params = {"key": api_key}

        try:
            response = requests.post(url, json=payload, headers=headers, params=params)
            data = response.json()
            return "candidates" in data
        except Exception as e:
            print(f"Lỗi khi xác thực API key: {e}")
            return False