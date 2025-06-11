import os
import requests
import urllib.parse
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class GoogleSearchClient:
    """Client cho Google Custom Search API."""
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cx = os.getenv("GOOGLE_SEARCH_ID")

    def search(self, query: str, num_results: int = 4, filter_by: Optional[str] = None, site_restrict: Optional[str] = None) -> List[Dict]:
        """Gọi Google Search API."""
        if not self.api_key or not self.cx:
            print("Lỗi: Thiếu GOOGLE_SEARCH_API_KEY hoặc GOOGLE_SEARCH_ID trong file .env")
            return self._get_fallback_results(query)
        
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.googleapis.com/customsearch/v1?q={encoded_query}&key={self.api_key}&cx={self.cx}&num={num_results}"
            
            if filter_by in ["d1", "w1", "m1", "y1"]:
                url += f"&dateRestrict={filter_by}"
            if site_restrict:
                url += f"&siteSearch={urllib.parse.quote(site_restrict)}"
            url += "&safe=active"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "items" not in data:
                    print(f"Không có kết quả tìm kiếm cho query: {query}")
                    return self._get_fallback_results(query)
                
                items = data.get("items", [])
                results = []
                for item in items:
                    result = {
                        "title": item.get("title", "Không có tiêu đề"),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "Không có mô tả")
                    }
                    results.append(result)
                return results
                
            elif response.status_code == 403:
                print(f"Lỗi 403: Không có quyền truy cập Google Search API. Có thể hết quota hoặc API key không đúng.")
                return self._get_fallback_results(query)
                
            elif response.status_code == 429:
                print(f"Lỗi 429: Đã vượt quá giới hạn request. Vui lòng thử lại sau.")
                return self._get_fallback_results(query)
                
            else:
                print(f"Lỗi khi tìm kiếm: {response.status_code} - {response.text}")
                return self._get_fallback_results(query)
                
        except requests.Timeout:
            print("Lỗi: Timeout khi gọi Google Search API")
            return self._get_fallback_results(query)
            
        except requests.RequestException as e:
            print(f"Lỗi kết nối: {e}")
            return self._get_fallback_results(query)
            
        except Exception as e:
            print(f"Lỗi không xác định: {e}")
            return self._get_fallback_results(query)

    def _get_fallback_results(self, query: str) -> List[Dict]:
        """Trả về kết quả fallback khi API không khả dụng."""
        return [
            {
                "title": f"Tìm kiếm về: {query}",
                "link": f"https://www.google.com/search?q={urllib.parse.quote(query)}",
                "snippet": f"Xin lỗi, dịch vụ tìm kiếm tạm thời không khả dụng. Bạn có thể tìm kiếm trực tiếp trên Google với từ khóa: '{query}'"
            },
            {
                "title": "Hướng dẫn sử dụng tìm kiếm",
                "link": "https://support.google.com/websearch/",
                "snippet": "Dịch vụ tìm kiếm web hiện tại đang gặp sự cố. Vui lòng thử lại sau hoặc sử dụng trực tiếp công cụ tìm kiếm Google."
            }
        ] 