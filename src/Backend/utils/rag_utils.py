from typing import List, Dict, Any
import numpy as np
import warnings

def calculate_relevance(query: str, result: Dict[str, Any]) -> float:
    """Tính điểm relevance của kết quả tìm kiếm với query."""
    try:
        query_terms = set(term.lower() for term in query.split() if len(term) > 2)
        if not query_terms:
            return 0.0
        
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        title_matches = sum(1 for term in query_terms if term in title)
        snippet_matches = sum(1 for term in query_terms if term in snippet)
        relevance = (title_matches * 0.7) + (snippet_matches * 0.3)
        max_possible = len(query_terms)
        
        if max_possible > 0:
            relevance = min(1.0, relevance / max_possible)
        else:
            relevance = 0.0
            
        return round(float(relevance), 2)
    except Exception as e:
        print(f"Warning: Error calculating relevance: {e}")
        return 0.0

def process_web_search_results(query: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Xử lý và sắp xếp kết quả tìm kiếm web theo relevance."""
    processed_results = []
    for result in search_results:
        try:
            processed_result = {
                'title': result.get('title', ''),
                'link': result.get('link', ''),
                'snippet': result.get('snippet', ''),
                'relevance': calculate_relevance(query, result)
            }
            processed_results.append(processed_result)
        except Exception as e:
            print(f"Warning: Error processing search result: {e}")
            continue
    
    try:
        processed_results.sort(key=lambda x: x.get('relevance', 0.0), reverse=True)
    except Exception as e:
        print(f"Warning: Error sorting results: {e}")
    
    return processed_results

def process_chunk_batch(model, chunks_batch: List[Any]) -> tuple:
    """Tạo embedding và mapping cho batch chunk."""
    try:
        batch_texts = [chunk[2] for chunk in chunks_batch]
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            batch_embeddings = model.encode(batch_texts, show_progress_bar=False)
        
        batch_mappings = []
        for chunk in chunks_batch:
            batch_mappings.append({
                'chunk_id': chunk[0],
                'file_id': chunk[1],
                'metadata': {
                    'file_name': chunk[3],
                    'chunk_index': chunk[4]
                }
            })
        
        embeddings_array = np.array(batch_embeddings, dtype='float32')
        
        if np.any(np.isnan(embeddings_array)) or np.any(np.isinf(embeddings_array)):
            print("Warning: Found NaN or infinite values in embeddings, replacing with zeros")
            embeddings_array = np.nan_to_num(embeddings_array, nan=0.0, posinf=0.0, neginf=0.0)
        
        return embeddings_array, batch_mappings
        
    except Exception as e:
        print(f"Error processing chunk batch: {e}")
        return np.array([], dtype='float32'), [] 