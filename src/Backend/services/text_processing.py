import re
import json
from typing import List, Dict, Any

class TextProcessing:

    def split_JSON_text(self, text: str) -> List[Dict[str, Any]]:
        """Tách văn bản chứa JSON thành danh sách các đối tượng JSON."""
        try:
            json_blocks = re.findall(r'\{[^{}]*\}', text)
            
            json_list = [json.loads(block) for block in json_blocks]
            return json_list
        except Exception as e:
            raise Exception(f"Lỗi khi tách text thành các đoạn JSON: {str(e)}")