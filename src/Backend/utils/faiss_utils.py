import os
import faiss
import numpy as np
from typing import Any, Optional, Tuple
import logging

from config.app_config import AppConfig

config = AppConfig()

logger = logging.getLogger(__name__)

def create_new_index(vector_size: int, num_vectors: int = 0, use_gpu: bool = False) -> Any:
    """Tạo FAISS index mới với thuật toán tối ưu dựa trên số lượng vectors."""
    
    if num_vectors < 1000:
        index = faiss.IndexFlatL2(vector_size)
        logger.info("Created IndexFlatL2 for small dataset")
    elif num_vectors < 10000:
        index = faiss.IndexHNSWFlat(vector_size, 32)
        index.hnsw.efConstruction = 200
        index.hnsw.efSearch = 50
        logger.info("Created IndexHNSWFlat for medium dataset")
    else:
        nlist = min(int(np.sqrt(num_vectors)), 4096)
        quantizer = faiss.IndexFlatL2(vector_size)
        index = faiss.IndexIVFFlat(quantizer, vector_size, nlist)
        logger.info(f"Created IndexIVFFlat with {nlist} clusters for large dataset")
    
    if use_gpu and faiss.get_num_gpus() > 0:
        try:
            res = faiss.StandardGpuResources()
            index = faiss.index_cpu_to_gpu(res, 0, index)
            logger.info("Moved index to GPU")
        except Exception as e:
            logger.warning(f"Failed to move index to GPU: {e}")
    
    return index

def create_optimized_index(vector_size: int, num_vectors: int, training_vectors: Optional[np.ndarray] = None) -> Any:
    """Tạo index được tối ưu hóa với training data."""
    
    if num_vectors < 1000:
        return create_new_index(vector_size, num_vectors)
    
    if num_vectors < 10000:
        index = faiss.IndexHNSWFlat(vector_size, 32)
        index.hnsw.efConstruction = 200
        index.hnsw.efSearch = 50
        logger.info("Created IndexHNSWFlat for optimized medium dataset")
    elif num_vectors < 50000:
        try:
            index = faiss.IndexHNSWPQ(vector_size, 8, 8)
            index.hnsw.efConstruction = 200
            index.hnsw.efSearch = 50
            logger.info("Created IndexHNSWPQ for optimized large dataset")
        except Exception as e:
            logger.warning(f"Failed to create HNSWPQ, falling back to HNSW: {e}")
            index = faiss.IndexHNSWFlat(vector_size, 32)
            index.hnsw.efConstruction = 200
            index.hnsw.efSearch = 50
    else:
        nlist = min(int(np.sqrt(num_vectors)), 4096)
        
        min_training_points = nlist * 39
        if training_vectors is not None and len(training_vectors) < min_training_points:
            logger.warning(f"Not enough training data ({len(training_vectors)}) for {nlist} clusters, using simpler index")
            index = faiss.IndexHNSWFlat(vector_size, 32)
            index.hnsw.efConstruction = 200
            index.hnsw.efSearch = 50
        else:
            try:
                index = faiss.IndexIVFPQ(faiss.IndexFlatL2(vector_size), vector_size, nlist, 8, 8)
                index.nprobe = min(32, nlist // 4)
                logger.info(f"Created IndexIVFPQ with {nlist} clusters for very large dataset")
            except Exception as e:
                logger.warning(f"Failed to create IVFPQ, falling back to IVFFlat: {e}")
                index = faiss.IndexIVFFlat(faiss.IndexFlatL2(vector_size), vector_size, nlist)
                index.nprobe = min(32, nlist // 4)
    
    if hasattr(index, 'is_trained') and not index.is_trained and training_vectors is not None:
        try:
            logger.info("Training index with sample data...")
            index.train(training_vectors.astype('float32'))
            logger.info("Index training completed")
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return faiss.IndexFlatL2(vector_size)
    
    return index

def save_index_to_disk(index: Any, chunk_id_mapping: list) -> None:
    """Lưu FAISS index và chunk mapping ra file với compression."""
    try:
        os.makedirs(os.path.dirname(config.FAISS_INDEX_PATH) or '.', exist_ok=True)
        
        faiss.write_index(index, config.FAISS_INDEX_PATH)
        
        np.savez_compressed(
            config.CHUNK_MAPPING_PATH.replace('.npy', '.npz'), 
            mapping=np.array(chunk_id_mapping, dtype=object)
        )
        
        logger.info(f"Saved index with {index.ntotal} vectors and {len(chunk_id_mapping)} mappings")
        
    except Exception as e:
        logger.error(f"Error saving index to disk: {e}")
        raise

def load_index_and_mapping() -> Tuple[Any, list]:
    """Load FAISS index và chunk mapping từ file."""
    try:
        index = faiss.read_index(config.FAISS_INDEX_PATH)
        
        npz_path = config.CHUNK_MAPPING_PATH.replace('.npy', '.npz')
        if os.path.exists(npz_path):
            data = np.load(npz_path, allow_pickle=True)
            chunk_id_mapping = data['mapping'].tolist()
        else:
            chunk_id_mapping = np.load(config.CHUNK_MAPPING_PATH, allow_pickle=True).tolist()
        
        logger.info(f"Loaded index with {index.ntotal} vectors and {len(chunk_id_mapping)} mappings")
        return index, chunk_id_mapping
        
    except Exception as e:
        logger.error(f"Error loading index from disk: {e}")
        raise

def optimize_search_params(index: Any, num_queries: int = 100) -> None:
    """Tối ưu hóa tham số search cho index."""
    try:
        if hasattr(index, 'hnsw'):
            if num_queries < 10:
                index.hnsw.efSearch = 100
            else:
                index.hnsw.efSearch = 50
                
        elif hasattr(index, 'nprobe'):
            total_clusters = index.nlist
            if num_queries < 10:
                index.nprobe = min(64, total_clusters // 2)
            else:
                index.nprobe = min(32, total_clusters // 4)
                
        logger.info("Optimized search parameters")
        
    except Exception as e:
        logger.warning(f"Failed to optimize search params: {e}")

def get_index_info(index: Any) -> dict:
    """Lấy thông tin về FAISS index."""
    info = {
        "type": type(index).__name__,
        "vector_size": index.d,
        "num_vectors": index.ntotal,
        "is_trained": getattr(index, 'is_trained', True)
    }
    
    if hasattr(index, 'hnsw') and index.hnsw is not None:
        try:
            info.update({
                "efConstruction": getattr(index.hnsw, 'efConstruction', 'N/A'),
                "efSearch": getattr(index.hnsw, 'efSearch', 'N/A'),
                "M": getattr(index.hnsw, 'M', 32)
            })
        except Exception as e:
            logger.warning(f"Could not get HNSW attributes: {e}")
            info["hnsw_info"] = "Available but attributes not accessible"
    
    if hasattr(index, 'nprobe'):
        try:
            info.update({
                "nlist": getattr(index, 'nlist', 'N/A'),
                "nprobe": getattr(index, 'nprobe', 'N/A')
            })
        except Exception as e:
            logger.warning(f"Could not get IVF attributes: {e}")
    
    return info 