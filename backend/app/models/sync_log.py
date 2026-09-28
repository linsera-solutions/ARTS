import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class SyncLog(Base):
    """
    SyncLog Entity (ARTS-TRA-010 Section 11 & 14)
    Maintains an audit trail of Google Forms / Google Sheets synchronization events.
    """
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False, default="Google Sheets / Forms")
    status = Column(String(50), nullable=False)  # Success, Partial, Failed
    total_rows = Column(Integer, nullable=False, default=0)
    created_count = Column(Integer, nullable=False, default=0)
    updated_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    error_summary = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
