from typing import List, Dict, Any
from clients.google_search_client import GoogleSearchClient
from services.web.query_analyzer import SearchQueryAnalyzer
from services.web.content_extractor import WebContentExtractor

class WebSearchService:
    def __init__(self):
        self.client = GoogleSearchClient()
        self.analyzer = SearchQueryAnalyzer()
        self.extractor = WebContentExtractor()

    async def perform_search(self, prompt: str) -> Dict[str, Any]:
        """Thực hiện tìm kiếm thông minh dựa trên phân tích prompt."""
        try:
            search_info = await self.analyzer.analyze(prompt)
            results = []
            main_query = search_info.get("main_query", prompt)
            alternative_queries = search_info.get("alternative_queries", [])
            query_type = search_info.get("query_type", "factual")
            time_relevance = search_info.get("time_relevance", "none")
            domain_specific = search_info.get("domain_specific")
            
            time_filter = None
            if time_relevance == "recent":
                time_filter = "m1"
            elif time_relevance == "very_recent":
                time_filter = "d1"
            
            # Thực hiện tìm kiếm dựa trên loại query
            if query_type in ["news", "recent"]:
                search_results = self.client.search(main_query, num_results=1, filter_by=time_filter or "w1")
                results.extend(search_results)
            elif query_type == "technical":
                search_results = self.client.search(main_query, num_results=2)
                results.extend(search_results)
                if domain_specific:
                    domain_results = self.client.search(main_query, num_results=2, site_restrict=domain_specific)
                    results.extend(domain_results)
            elif query_type == "comparison":
                search_results = self.client.search(main_query, num_results=2)
                results.extend(search_results)
                for alt_query in alternative_queries[:2]:
                    alt_results = self.client.search(alt_query, num_results=1)
                    results.extend(alt_results)
            else:
                search_results = self.client.search(main_query, num_results=1, filter_by=time_filter)
                results.extend(search_results)
                if alternative_queries:
                    alt_results = self.client.search(alternative_queries[0], num_results=1)
                    results.extend(alt_results)
            
            # Format response properly
            return {
                "results": results,
                "query_info": search_info,
                "total_results": len(results),
                "status": "success"
            }
            
        except Exception as e:
            print(f"Error in web search: {str(e)}")
            return {
                "results": [],
                "query_info": {"main_query": prompt, "query_type": "factual"},
                "total_results": 0,
                "status": "error",
                "error": str(e)
            }

    def get_page_content(self, url: str) -> Dict[str, str]:
        """Lấy nội dung chính của một trang web."""
        try:
            return self.extractor.extract(url)
        except Exception as e:
            return {
                "error": f"Lỗi khi lấy nội dung trang: {str(e)}",
                "url": url,
                "title": "",
                "content": ""
            } 