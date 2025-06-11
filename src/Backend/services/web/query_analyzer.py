import re
from typing import Dict, Union, List
from models.llm import LLM
from services.text_processing import TextProcessing

class SearchQueryAnalyzer:
    
    def __init__(self):
        self.llm = LLM()
        self.text_processing = TextProcessing()

    async def analyze(self, prompt: str) -> Dict[str, Union[str, List[str]]]:
        """Phân tích prompt để trích xuất thông tin tìm kiếm."""
        simple_time_keywords = {
            "hôm nay": "very_recent", 
            "gần đây": "recent",
            "mới nhất": "recent",
            "tuần này": "recent",
            "tháng này": "recent",
            "năm nay": "recent"
        }
        time_relevance = "none"
        for keyword, value in simple_time_keywords.items():
            if keyword in prompt.lower():
                time_relevance = value
                break
        domain_specific = None
        url_pattern = re.compile(r'https?://(?:www\.)?([a-zA-Z0-9.-]+)(?:/|$)')
        url_match = url_pattern.search(prompt)
        if url_match:
            domain_specific = url_match.group(1)
        if len(prompt) > 10 and ("?" in prompt or any(x in prompt.lower() for x in ["so sánh", "tìm", "nghiên cứu"])):
            analysis_prompt = f"""Phân tích câu hỏi: \"{prompt}\"
                Trả về JSON ngắn gọn:
                {{
                "main_query": "câu truy vấn chính, ngắn gọn",
                "alternative_queries": ["truy vấn thay thế 1", "truy vấn thay thế 2"],
                "query_type": "factual|technical|opinion|news|comparison"
                }}
            """
            try:
                response_text = await self.llm.generateContent(analysis_prompt)
                json_results = self.text_processing.split_JSON_text(response_text)
                if json_results and len(json_results) > 0:
                    result = json_results[0]
                    if time_relevance != "none":
                        result["time_relevance"] = time_relevance
                    if domain_specific:
                        result["domain_specific"] = domain_specific
                    return result
            except Exception:
                pass
        return {
            "main_query": prompt,
            "alternative_queries": [],
            "time_relevance": time_relevance,
            "domain_specific": domain_specific,
            "query_type": "factual"
        } 