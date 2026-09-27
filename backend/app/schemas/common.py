from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class DatabaseHealthStatus(BaseModel):
    postgres_connected: bool
    supabase_client_ready: bool
    message: str


class HealthCheckResponse(BaseModel):
    status: str
    environment: str
    version: str
    database: DatabaseHealthStatus
