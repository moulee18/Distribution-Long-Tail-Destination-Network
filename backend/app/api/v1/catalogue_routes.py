import os
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.schemas.app_schemas import ImportSummary
from backend.app.services.catalogue import catalogue_service
from backend.app.core.errors import IncuBrixException, ErrorCode

router = APIRouter(prefix="/catalogue", tags=["Catalogue"])

@router.post("/import", response_model=ImportSummary)
async def import_catalogue_csv(
    file: Optional[UploadFile] = File(None),
    raw_csv: Optional[str] = Form(None),
    allow_local: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    if file:
        content_bytes = await file.read()
        csv_text = content_bytes.decode("utf-8", errors="replace")
    elif raw_csv:
        csv_text = raw_csv
    else:
        raise IncuBrixException(
            ErrorCode.VALIDATION_ERROR,
            "Either a CSV file upload or 'raw_csv' form parameter must be provided.",
            status_code=400,
        )

    summary = await catalogue_service.import_csv_data(csv_text, db, allow_local=allow_local)
    return summary

@router.post("/seed-full", response_model=ImportSummary)
async def seed_full_150_catalogue(db: AsyncSession = Depends(get_db)):
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "fixtures", "destinations_150.csv"))
    if not os.path.exists(csv_path):
        raise IncuBrixException(ErrorCode.RESOURCE_NOT_FOUND, "Seed CSV fixtures/destinations_150.csv not found", 404)
    with open(csv_path, "r", encoding="utf-8") as f:
        csv_text = f.read()
    return await catalogue_service.import_csv_data(csv_text, db, allow_local=True)

