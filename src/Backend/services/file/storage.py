import os
from fastapi import UploadFile
from typing import List, Dict, Any

UPLOAD_FOLDER = "upload"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class FileStorage:

    def save_file(self, file: UploadFile) -> str:
        """Lưu file tải lên vào thư mục upload."""
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        return file_path

    def delete_file(self, file_name: str) -> bool:
        """Xóa file khỏi thư mục upload."""
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def list_files(self) -> List[Dict[str, Any]]:
        """Liệt kê tất cả các file trong thư mục upload."""
        files = []
        for file_name in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, file_name)
            size = os.path.getsize(file_path)
            files.append({"name": file_name, "size": size, "path": file_path})
        return files 