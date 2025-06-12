import os
import time
import logging
import asyncio
import sys
from typing import List, Dict, Tuple, Optional, Set, Any
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from services.vector_db import VectorDBService
from models.llm import LLM

from config.torch_config import device, suppress_pytorch_warnings

from utils.rag_file_utils import (
    get_uploaded_files_info, process_file_changes
)
from utils.faiss_utils import (
    create_new_index, create_optimized_index, save_index_to_disk, 
    load_index_and_mapping, optimize_search_params, get_index_info
)
from utils.rag_utils import calculate_relevance, process_web_search_results, process_chunk_batch
from config.app_config import AppConfig

config = AppConfig()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_service.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class RAGService:
    
    def __init__(self, upload_dir: str = "upload") -> None:
        """Initialize RAGService with required components."""
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        self.vector_db = VectorDBService()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm = LLM()
        self.chunk_id_mapping = []
        self.index = None
        self.use_gpu = faiss.get_num_gpus() > 0
        self.optimal_batch_size = self._calculate_optimal_batch_size()
        self._initialize_service()

    def _calculate_optimal_batch_size(self) -> int:
        """Tính toán batch size tối ưu dựa trên memory và GPU availability."""
        try:
            import psutil
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            
            if self.use_gpu:
                if available_memory_gb > 8:
                    return 200
                elif available_memory_gb > 4:
                    return 100
                else:
                    return 50
            else:
                if available_memory_gb > 16:
                    return 100
                elif available_memory_gb > 8:
                    return 50
                else:
                    return 25
        except ImportError:
            logger.warning("psutil not available, using default batch size")
            return 50

    def _initialize_service(self) -> None:
        """Initialize the RAG service components."""
        try:
            self.load_or_create_index()
            logger.info("RAGService initialized successfully")
            
            if self.index:
                info = get_index_info(self.index)
                logger.info(f"Index info: {info}")
                
        except Exception as e:
            logger.error(f"Failed to initialize RAGService: {str(e)}")
            raise

    def _get_database_files_info(self) -> Tuple[Set[str], Dict[str, float]]:
        """Retrieve information about files stored in the database."""
        try:
            db_files = self.vector_db.get_all_files()
            db_file_names = {file[1] for file in db_files}
            db_file_mtimes = self.vector_db.database_manager.get_file_modification_times()
            logger.debug(f"Retrieved info for {len(db_file_names)} files from database")
            return db_file_names, db_file_mtimes
        except Exception as e:
            logger.error(f"Error getting file info from database: {str(e)}")
            return set(), {}

    async def _process_modified_files(self, file_names: List[str]) -> None:
        """Process new or modified files."""
        if not file_names:
            return
        logger.info(f"Starting processing of {len(file_names)} new/modified files")
        for file_name in file_names:
            file_path = os.path.join(self.upload_dir, file_name)
            try:
                start_time = time.time()
                await self.vector_db.process_file(file_path)
                process_time = time.time() - start_time
                logger.info(f"Processed file {file_name} in {process_time:.2f}s")
            except FileNotFoundError:
                logger.warning(f"File not found: {file_name}")
            except PermissionError:
                logger.error(f"Permission denied reading file: {file_name}")
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {str(e)}", exc_info=True)

    def _process_deleted_files(self, deleted_files: List[str]) -> None:
        """Process files that have been deleted from the upload directory."""
        if not deleted_files:
            return
        logger.info(f"Starting processing of {len(deleted_files)} deleted files")
        for file_name in deleted_files:
            try:
                self.vector_db.delete_file(file_name)
                logger.info(f"Removed file {file_name} from database")
            except Exception as e:
                logger.error(f"Error removing file {file_name}: {str(e)}")

    async def check_and_update_files(self) -> bool:
        """Check for and process any changes in the upload directory."""
        try:
            upload_info = get_uploaded_files_info(self.upload_dir)
            db_file_names, db_file_mtimes = self._get_database_files_info()
            new_or_modified, deleted = process_file_changes(
                upload_info, db_file_names, db_file_mtimes
            )
            if not new_or_modified and not deleted:
                logger.debug("No changes detected in upload directory")
                return False
            
            files_changed = False
            
            if deleted:
                self._process_deleted_files(deleted)
                files_changed = True
                
            if new_or_modified:
                await self._process_modified_files(new_or_modified)
                files_changed = True
            
            # Rebuild FAISS index nếu có thay đổi
            if files_changed:
                logger.info("Files changed, rebuilding optimized FAISS index...")
                await self._rebuild_index_from_database()
            
            logger.info("Successfully updated database and FAISS index")
            return True
        except Exception as e:
            logger.critical(f"LỖI NGHIÊM TRỌNG khi kiểm tra và cập nhật files: {str(e)}", exc_info=True)
            raise

    def load_or_create_index(self) -> None:
        """Load or create a new FAISS index and chunk mapping."""
        try:
            index_exists = os.path.exists(config.FAISS_INDEX_PATH)
            mapping_exists = os.path.exists(config.CHUNK_MAPPING_PATH) or os.path.exists(config.CHUNK_MAPPING_PATH.replace('.npy', '.npz'))
            
            if index_exists and mapping_exists:
                logger.info("Loading FAISS index and chunk mapping from disk...")
                self.index, self.chunk_id_mapping = load_index_and_mapping()
                logger.info(
                    f"Loaded index with {self.index.ntotal} vectors and "
                    f"{len(self.chunk_id_mapping)} chunk mappings"
                )
                
                optimize_search_params(self.index)
                return
                
            logger.info("Index files not found or corrupted, creating new index...")
            self.index = create_new_index(self.model.get_sentence_embedding_dimension(), 0, self.use_gpu)
            self.chunk_id_mapping = []
            save_index_to_disk(self.index, self.chunk_id_mapping)
        except Exception as e:
            logger.critical(f"Critical error initializing index: {str(e)}")
            raise

    def calculate_relevance(self, query: str, result: Dict[str, Any]) -> float:
        """Tính điểm relevance của kết quả tìm kiếm với query."""
        return calculate_relevance(query, result)

    def process_chunk_batch(self, chunks_batch: List[Any]) -> Tuple[np.ndarray, List[Dict]]:
        """Tạo embedding và mapping cho batch chunk."""
        return process_chunk_batch(self.model, chunks_batch)

    def process_web_search_results(self, query: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Xử lý và sắp xếp kết quả tìm kiếm web theo relevance."""
        return process_web_search_results(query, search_results)

    async def _rebuild_index_from_database(self) -> None:
        """Xây dựng lại FAISS index từ dữ liệu trong database với tối ưu hóa."""
        try:
            all_chunks = self.vector_db.get_all_chunks()
            
            if not all_chunks:
                logger.info("No chunks found in database")
                return
            
            num_chunks = len(all_chunks)
            logger.info(f"Rebuilding optimized FAISS index from {num_chunks} chunks")
            
            training_data = None
            if num_chunks > 1000:
                sample_size = min(max(num_chunks // 10, 100), 10000)
                sample_indices = np.random.choice(num_chunks, sample_size, replace=False)
                sample_texts = [all_chunks[i][1] for i in sample_indices]
                training_data = self.model.encode(sample_texts, show_progress_bar=False)
                training_data = np.array(training_data, dtype='float32')
                logger.info(f"Created training data with {len(training_data)} samples")
            
            vector_size = self.model.get_sentence_embedding_dimension()
            self.index = create_optimized_index(vector_size, num_chunks, training_data)
            self.chunk_id_mapping = []
            
            batch_size = self.optimal_batch_size
            logger.info(f"Processing chunks with batch size: {batch_size}")
            
            for i in range(0, num_chunks, batch_size):
                batch = all_chunks[i:i + batch_size]
                
                texts = [chunk[1] for chunk in batch]  # chunk[1] là content
                embeddings = self.model.encode(texts, show_progress_bar=False)
                embeddings_array = np.array(embeddings, dtype='float32')
                
                if np.any(np.isnan(embeddings_array)) or np.any(np.isinf(embeddings_array)):
                    logger.warning(f"Found invalid embeddings in batch {i//batch_size + 1}, cleaning...")
                    embeddings_array = np.nan_to_num(embeddings_array, nan=0.0, posinf=0.0, neginf=0.0)
                
                self.index.add(embeddings_array)
                
                for chunk in batch:
                    chunk_mapping = {
                        'chunk_id': chunk[0],  # chunk[0] là ID
                        'content': chunk[1],   # chunk[1] là content
                        'source': chunk[2],    # chunk[2] là source file
                        'chunk_index': chunk[3] # chunk[3] là chunk_index
                    }
                    self.chunk_id_mapping.append(chunk_mapping)
                
                if (i // batch_size + 1) % 10 == 0:
                    logger.info(f"Processed {i + len(batch)}/{num_chunks} chunks")
            
            optimize_search_params(self.index)
            
            save_index_to_disk(self.index, self.chunk_id_mapping)
            
            info = get_index_info(self.index)
            logger.info(f"FAISS index rebuilt successfully: {info}")
            
        except Exception as e:
            logger.error(f"Error rebuilding FAISS index: {str(e)}", exc_info=True)
            raise

    async def query(self, question: str, k: int = 5) -> str:
        """Truy vấn hệ thống RAG với câu hỏi đầu vào và trả về câu trả lời."""
        try:
            if self.index is None or self.index.ntotal == 0:
                logger.info("Index is empty, rebuilding from database...")
                await self._rebuild_index_from_database()
            
            if self.index is None or self.index.ntotal == 0:
                return "Không có dữ liệu để truy vấn. Vui lòng upload tài liệu trước."
            
            optimize_search_params(self.index, num_queries=1)
            
            query_embedding = self.model.encode([question])
            query_embedding = np.array(query_embedding, dtype='float32')
            
            if np.any(np.isnan(query_embedding)) or np.any(np.isinf(query_embedding)):
                logger.warning("Invalid query embedding, cleaning...")
                query_embedding = np.nan_to_num(query_embedding, nan=0.0, posinf=0.0, neginf=0.0)
            
            search_k = min(k, self.index.ntotal)
            D, I = self.index.search(query_embedding, k=search_k)
            
            context_chunks = []
            chunk_scores = []
            
            for i, idx in enumerate(I[0]):
                if idx < len(self.chunk_id_mapping) and idx >= 0:
                    chunk_mapping = self.chunk_id_mapping[idx]
                    chunk_id = chunk_mapping.get('chunk_id')
                    if chunk_id:
                        chunk_content = self.vector_db.get_chunk_by_id(chunk_id)
                        if chunk_content:
                            context_chunks.append(chunk_content)
                            chunk_scores.append(D[0][i])
            
            if not context_chunks:
                return "Không tìm thấy thông tin liên quan trong tài liệu đã upload."
            
            score_threshold = np.mean(chunk_scores) if chunk_scores else float('inf')
            filtered_chunks = [
                chunk for chunk, score in zip(context_chunks, chunk_scores)
                if score <= score_threshold * 1.2
            ]
            
            context = "\n\n".join(filtered_chunks[:3])
            
            try:
                logger.info(f"Found {len(context_chunks)} relevant chunks, using {len(filtered_chunks[:3])}")
            except UnicodeEncodeError:
                logger.info(f"Found {len(context_chunks)} relevant chunks")
            
            response = await self.llm.generateContent(
                prompt=question,
                rag_response=context
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG query: {str(e)}", exc_info=True)
            return f"Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi: {str(e)}"

    def get_index_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê về FAISS index."""
        if not self.index:
            return {"error": "No index available"}
        
        stats = get_index_info(self.index)
        stats.update({
            "mapping_size": len(self.chunk_id_mapping),
            "optimal_batch_size": self.optimal_batch_size,
            "gpu_available": self.use_gpu,
        })
        
        return stats
