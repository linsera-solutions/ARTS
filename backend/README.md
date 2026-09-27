# ARTS - Backend

Clean Python + FastAPI REST API backend for the Applicant Review & Team Selection System (ARTS) MVP.

## Tech Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Configuration**: Pydantic & Pydantic-Settings

## Getting Started

### 1. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` if custom configurations are needed:
```bash
copy .env.example .env
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. API Documentation
- Interactive Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`
- Health Check: `http://localhost:8000/health`
- API Status: `http://localhost:8000/api/v1/status`
