from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "ARTS API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, testing, staging, production
    DEBUG: bool = True

    # Backend Server Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # CORS configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Database Configuration (Supabase PostgreSQL direct URI)
    DATABASE_URL: Optional[str] = None

    # Supabase Client Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None  # Anon / Public Key
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None  # Admin/Service Role Key (Backend Only)

    # Google Sheets / Forms Intake Configuration
    GOOGLE_SHEETS_SPREADSHEET_ID: Optional[str] = None
    GOOGLE_SHEETS_RANGE: str = "Form Responses 1!A1:Z"
    GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = None
    GOOGLE_SERVICE_ACCOUNT_JSON: Optional[str] = None
    GOOGLE_WEBHOOK_SECRET: Optional[str] = None  # Secret token for Google Apps Script webhook calls

    # Authentication & JWT Configuration
    JWT_SECRET: str = "arts-recruiter-jwt-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours default recruiter session

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def sqlalchemy_database_uri(self) -> Optional[str]:
        """
        Ensures the SQLAlchemy database URI uses the correct driver prefix.
        PostgreSQL connection strings starting with 'postgres://' are normalized to 'postgresql://'.
        """
        if not self.DATABASE_URL:
            return None
        if self.DATABASE_URL.startswith("postgres://"):
            return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
