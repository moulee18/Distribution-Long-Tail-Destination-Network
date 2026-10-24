import io
import os
import socket
import uuid
from typing import Optional, Tuple
from minio import Minio
from backend.app.core.config import settings
from backend.app.core.logging import logger

class StorageService:
    def __init__(self):
        self.minio_client: Optional[Minio] = None
        self._init_client()

    def _init_client(self):
        try:
            host_port = settings.MINIO_ENDPOINT.split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 9000
            with socket.create_connection((host, port), timeout=0.3):
                pass
            self.minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            if not self.minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
                self.minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
        except Exception:
            self.minio_client = None

    def save_file(self, content_bytes: bytes, filename: str, content_type: str = "application/octet-stream") -> Tuple[str, str]:
        ext = filename.split(".")[-1] if "." in filename else "bin"
        unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
        
        # Try MinIO first
        if self.minio_client:
            try:
                self.minio_client.put_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=unique_name,
                    data=io.BytesIO(content_bytes),
                    length=len(content_bytes),
                    content_type=content_type,
                )
                url = f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{unique_name}"
                return unique_name, url
            except Exception as e:
                logger.warning(f"MinIO put_object failed, using local storage: {str(e)}")

        # Local storage fallback
        local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage_uploads")
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, unique_name)
        with open(local_path, "wb") as f:
            f.write(content_bytes)
        url = f"/api/v1/storage/files/{unique_name}"
        return unique_name, url

storage_service = StorageService()
