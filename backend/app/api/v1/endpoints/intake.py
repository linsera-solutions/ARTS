from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.sync_log import SyncLog
from app.services.google_sync_service import google_sync_service
from app.schemas.intake import (
    GoogleFormsWebhookPayload,
    GoogleCsvIntakeRequest,
    GoogleSyncStatusResponse,
    SyncLogRead,
)
from app.schemas.application import (
    IntakeResultItem,
    IntakeSummaryResponse,
)
from app.schemas.common import ResponseEnvelope
from app.core.exceptions import BadRequestException

router = APIRouter()


@router.post(
    "/google-forms/webhook",
    response_model=ResponseEnvelope[IntakeResultItem],
    status_code=status.HTTP_200_OK,
    summary="Receive single Google Forms submission webhook",
    description="Webhook endpoint intended for Google Apps Script trigger onFormSubmit.",
)
def handle_google_forms_webhook(
    payload: GoogleFormsWebhookPayload,
    db: Session = Depends(get_db),
) -> ResponseEnvelope[IntakeResultItem]:
    res = google_sync_service.process_webhook_payload(db=db, payload=payload)
    return ResponseEnvelope(data=res, message=res.reason)


@router.post(
    "/google-forms/csv",
    response_model=ResponseEnvelope[IntakeSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Ingest raw CSV text from Google Forms export",
    description="Accepts a raw CSV text string exported from Google Forms / Sheets response sheet.",
)
def handle_google_csv_text(
    payload: GoogleCsvIntakeRequest,
    db: Session = Depends(get_db),
) -> ResponseEnvelope[IntakeSummaryResponse]:
    res = google_sync_service.process_csv_content(
        db=db,
        csv_text=payload.csv_content,
        source_name=payload.source_name or "Google Forms CSV Export",
    )
    return ResponseEnvelope(
        data=res,
        message=f"CSV processing complete: {res.accepted} created, {res.updated} updated, {res.rejected} rejected.",
    )


@router.post(
    "/google-forms/upload-csv",
    response_model=ResponseEnvelope[IntakeSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Upload CSV file exported from Google Forms/Sheets",
    description="Accepts a multipart/form-data .csv file containing Google Forms responses.",
)
async def handle_google_csv_upload(
    file: UploadFile = File(..., description="The .csv file exported from Google Forms/Sheets"),
    source_name: Optional[str] = Form("Google Forms CSV File Upload"),
    db: Session = Depends(get_db),
) -> ResponseEnvelope[IntakeSummaryResponse]:
    if not file.filename.lower().endswith(".csv"):
        raise BadRequestException("Uploaded file must be a .csv file.")

    content_bytes = await file.read()
    try:
        csv_text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            csv_text = content_bytes.decode("latin-1")
        except Exception:
            raise BadRequestException("Unable to decode CSV file content with UTF-8 or Latin-1.")

    res = google_sync_service.process_csv_content(
        db=db,
        csv_text=csv_text,
        source_name=f"{source_name} ({file.filename})",
    )
    return ResponseEnvelope(
        data=res,
        message=f"Uploaded CSV processing complete: {res.accepted} created, {res.updated} updated, {res.rejected} rejected.",
    )


@router.get(
    "/google-sheets/status",
    response_model=ResponseEnvelope[GoogleSyncStatusResponse],
    summary="Get Google intake integration status",
    description="Checks Google configuration, last sync log, and total records synced.",
)
def get_google_sync_status(
    db: Session = Depends(get_db),
) -> ResponseEnvelope[GoogleSyncStatusResponse]:
    status_data = google_sync_service.get_sync_status(db=db)
    return ResponseEnvelope(data=status_data)


@router.get(
    "/logs",
    response_model=ResponseEnvelope[List[SyncLogRead]],
    summary="List intake synchronization logs",
    description="Retrieves chronological audit logs of CSV/webhook ingestion events.",
)
def get_sync_logs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ResponseEnvelope[List[SyncLogRead]]:
    logs = (
        db.query(SyncLog)
        .order_by(SyncLog.synced_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return ResponseEnvelope(data=logs)