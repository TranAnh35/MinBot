import os
import time
from pathlib import Path
from typing import Dict, Set, Tuple

from config.app_config import AppConfig

config = AppConfig()

def get_uploaded_files_info(upload_dir: str) -> Dict[str, float]:
    """Retrieve information about files in the upload directory."""
    files_info = {}
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        return files_info
    for filename in os.listdir(upload_dir):
        file_ext = Path(filename).suffix.lower()
        if file_ext not in config.SUPPORTED_EXTENSIONS:
            continue
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            try:
                mtime = os.path.getmtime(file_path)
                files_info[filename] = mtime
            except (OSError, IOError):
                continue
    return files_info

def process_file_changes(upload_info: Dict[str, float], db_file_names: Set[str], db_file_mtimes: Dict[str, float]) -> Tuple[list, list]:
    """Identify new, modified, or deleted files based on database timestamps."""
    new_or_modified = []
    for file_name, mtime in upload_info.items():
        is_new = file_name not in db_file_names
        is_modified = not is_new and file_name in db_file_mtimes and mtime > db_file_mtimes[file_name]
        if is_new or is_modified:
            new_or_modified.append(file_name)
    deleted = list(db_file_names - upload_info.keys())
    return new_or_modified, deleted 