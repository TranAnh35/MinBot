import requests
from bs4 import BeautifulSoup
import re
from typing import Dict

class WebContentExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def extract(self, url: str) -> Dict[str, str]:
        """Lấy nội dung chính của trang web."""
        try:
            if not url.startswith(('http://', 'https://')):
                return {"error": "URL không hợp lệ. URL phải bắt đầu bằng http:// hoặc https://"}
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return {"error": f"Không thể truy cập trang. Mã trạng thái: {response.status_code}"}
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.title.string if soup.title else "Không có tiêu đề"
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'iframe', 'noscript']):
                element.decompose()
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|article|body|main', re.I))
            if main_content:
                text_content = main_content.get_text(separator="\n", strip=True)
            else:
                text_content = soup.body.get_text(separator="\n", strip=True) if soup.body else soup.get_text(separator="\n", strip=True)
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
            return {
                "title": title,
                "content": text_content,
                "url": url
            }
        except Exception as e:
            return {"error": f"Lỗi khi xử lý nội dung trang: {str(e)}"} 