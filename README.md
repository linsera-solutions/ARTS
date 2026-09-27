# ARTS (Applicant Review & Team Selection System)

## Project Overview

ARTS is an MVP decision-support recruitment system designed for a NASA Space Apps Challenge team workflow. It enables the Team Lead / Recruiter to efficiently ingest, organize, review, and select candidates from Google Forms applicant submissions into defined project roles.

### Operational Guardrails
- **Human-in-the-loop**: Final selections and evaluations remain human decisions.
- **No Applicant-Facing Portal**: Candidate intake occurs via Google Forms; ARTS is an internal recruiter console.
- **No Autonomous Ranking**: Candidates are not assigned mandatory black-box numeric scores or autonomous rankings.

### Approved Target Team Roles
1. **Role 1**: Team Lead + Product/Game Concept Lead / Research & Presentation
2. **Role 2**: Game/App Developer
3. **Role 3**: UI/UX & Visual Designer
4. **Role 4**: Space/Science Research + Game Logic

---

## Approved Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 + Vite 6 (JavaScript) |
| **Backend** | Python 3.10+ + FastAPI |
| **API Architecture** | RESTful JSON API |
| **Database** | PostgreSQL via Supabase *(Integration in upcoming milestone)* |
| **Version Control** | Git + GitHub |
| **API Testing** | Postman |

---

## Project Structure

```text
arts-project/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/              # API endpoints and routers
│   │   │   └── v1/
│   │   │       ├── api.py    # Route definitions
│   │   │       └── __init__.py
│   │   ├── core/             # Application config and settings
│   │   │   ├── config.py
│   │   │   └── __init__.py
│   │   ├── main.py           # FastAPI entrypoint with CORS & routes
│   │   └── __init__.py
│   ├── .env.example          # Backend environment variables template
│   ├── requirements.txt      # Python dependencies
│   └── README.md             # Backend setup guide
├── frontend/                 # React + Vite frontend
│   ├── src/
│   │   ├── App.css
│   │   ├── App.jsx           # Main React root component
│   │   ├── index.css
│   │   └── main.jsx          # React DOM entrypoint
│   ├── index.html            # HTML template
│   ├── package.json          # Frontend npm dependencies and scripts
│   ├── vite.config.js        # Vite configuration
│   ├── .env.example          # Frontend environment variables template
│   └── README.md             # Frontend setup guide
├── .env.example              # Root environment reference
├── .gitignore                # Stack-specific ignore rules
└── README.md                 # Project root documentation
```

---

## Local Development Quickstart

### Prerequisites
- **Node.js** (v18+ or v20+) and **npm**
- **Python** (v3.10+) and **pip**
- **Git**

---

### Backend Setup

1. Open a terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     python -m venv venv
     venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   - API Health: `http://localhost:8000/health`
   - Interactive Swagger Docs: `http://localhost:8000/api/v1/docs`

---

### Frontend Setup

1. Open a new terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

   - Frontend URL: `http://localhost:5173`
