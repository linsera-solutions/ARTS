from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema


class GoogleFormsWebhookPayload(BaseSchema):
    """
    Payload sent by Google Apps Script onFormSubmit trigger or direct webhook.
    """
    secret_token: Optional[str] = Field(None, description="Optional authentication token matching GOOGLE_WEBHOOK_SECRET")
    timestamp: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    motivation: Optional[str] = None
    availability: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    raw_responses: Optional[Dict[str, Any]] = None


class GoogleCsvIntakeRequest(BaseSchema):
    """
    Direct CSV text payload for intake.
    """
    csv_content: str = Field(..., description="Raw CSV string from Google Forms export")
    source_name: Optional[str] = Field("Google Forms CSV Export", description="Source description")


class GoogleSyncStatusResponse(BaseSchema):
    configured: bool
    spreadsheet_id_configured: bool
    service_account_configured: bool
    webhook_enabled: bool
    last_sync: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    total_synced: int = 0


class SyncLogRead(BaseSchema):
    id: UUID
    source: str
    status: str
    total_rows: int
    created_count: int
    updated_count: int
    rejected_count: int
    error_summary: Optional[str] = None
    details: Optional[Any] = None
    synced_at: datetime
