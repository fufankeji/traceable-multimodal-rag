from fastapi import UploadFile
import os

class FileHandler:
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_file(self, file: UploadFile) -> dict:
        file_location = os.path.join(self.upload_dir, file.filename)
        with open(file_location, "wb") as f:
            f.write(file.file.read())
        return {
            "filename": file.filename,
            "id": self.generate_unique_id(file.filename),
            "status": "uploaded"
        }

    def generate_unique_id(self, filename: str) -> str:
        return f"{filename}_{os.urandom(4).hex()}"  # Simple unique ID generation

    def read_file(self, filename: str) -> bytes:
        file_location = os.path.join(self.upload_dir, filename)
        with open(file_location, "rb") as f:
            return f.read()