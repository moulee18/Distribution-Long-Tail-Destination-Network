import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from backend.app.storage.s3 import storage_service
from backend.app.core.errors import IncuBrixException, ErrorCode

router = APIRouter(prefix="/storage", tags=["Storage"])

@router.post("/upload")
async def upload_asset(file: UploadFile = File(...)):
    content_bytes = await file.read()
    key, url = storage_service.save_file(content_bytes, file.filename, file.content_type or "application/octet-stream")
    return {
        "filename": file.filename,
        "key": key,
        "url": url,
        "size_bytes": len(content_bytes),
        "content_type": file.content_type,
    }

@router.get("/files/{filename}")
async def get_local_stored_file(filename: str):
    local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage_uploads")
    path = os.path.join(local_dir, filename)
    if not os.path.exists(path):
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, f"File {filename} not found", 404)
    return FileResponse(path)
