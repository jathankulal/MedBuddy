# MedBuddy — Your Personal Health Context Copilot

MedBuddy is a full-stack, demo-ready prototype combining a FastAPI backend, persistent JSON storage, a ChromaDB vector database with PyMuPDF RAG extraction, a fail-closed safety engine, and a React 19 frontend styled with Tailwind CSS.

---

## 1. System Overview

- **Backend**: FastAPI on Python 3.12+ with atomic JSON persistence, ChromaDB vector indexing, PyMuPDF PDF parser, Sentence-Transformers embeddings, and Gemini integration.
- **Frontend**: React 19 + Vite + Tailwind CSS 4 + Axios client.
- **Safety Engine**: Independent rule engine evaluating candidate medications (exact duplicates, ingredient overlaps, allergy conflicts) and user chat messages (emergency detection bypass).

---

## 2. Prerequisites

- **Python**: 3.12 or higher
- **Node.js**: v18.0.0 or higher (v20+ recommended)
- **PowerShell**: Windows PowerShell 5.1 or PowerShell Core 7+

---

## 3. Backend Setup

### A. Environment & Dependencies

Open a PowerShell terminal in the project directory:

```powershell
cd D:\classhack\MedBuddy\MedBuddy

# Create virtual environment if not already present
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
```

### B. Backend Configuration (`.env`)

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Ensure the following variables are configured in `.env`:

```env
APP_NAME=MedBuddy
APP_ENV=development
APP_DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
DATA_DIR=./data
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501

# Gemini API Key (Backend-only. Never expose to frontend or git).
# If omitted or unconfigured, emergency detection and safety rules operate normally,
# and chat requests requiring Gemini return clear configuration guidance.
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

---

## 4. Frontend Setup

Open a separate PowerShell terminal in the `frontend-react` folder:

```powershell
cd D:\classhack\MedBuddy\MedBuddy\frontend-react

# Install npm dependencies
npm install

# Ensure environment file is created
Copy-Item .env.example .env
```

The frontend `.env` contains:

```env
VITE_API_BASE_URL=http://localhost:8000
```

*(Note: Never place API keys or Gemini credentials in the frontend `.env` or bundle).*

---

## 5. Running the Application

### Terminal 1: Start Backend (FastAPI)

```powershell
cd D:\classhack\MedBuddy\MedBuddy
.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

- Local API: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

### Terminal 2: Start Frontend (React + Vite)

```powershell
cd D:\classhack\MedBuddy\MedBuddy\frontend-react
npm run dev
```

- Local Web App: `http://localhost:5173`

---

## 6. Running Tests

### Backend Tests (All Test Suites)

```powershell
cd D:\classhack\MedBuddy\MedBuddy
$env:TRANSFORMERS_OFFLINE="1"
$env:HF_HUB_OFFLINE="1"
$env:ANONYMIZED_TELEMETRY="False"
.venv\Scripts\python.exe -m pytest tests -v --import-mode=importlib
```

### Safety Engine Tests

```powershell
cd D:\classhack\MedBuddy\MedBuddy
.venv\Scripts\python.exe -m pytest tests/safety -v
```

### Frontend Build & Lint Checks

```powershell
cd D:\classhack\MedBuddy\MedBuddy\frontend-react
npm run lint
npm run build
```

---

## 7. End-to-End Demo Journey

Follow this step-by-step path to demonstrate MedBuddy:

1. **Access Workspace**: Open `http://localhost:5173`. Click **"Enter Demo Workspace"** to enter the single-user prototype dashboard. Notice the top status pill displays **"Backend Connected"**.
2. **Health Profile**:
   - Navigate to **Health Profile**.
   - Enter name: `Jane Doe`, Date of birth: `1988-06-15`.
   - In Allergies: enter `Penicillin` on its own line.
   - In Conditions: enter `Mild Asthma`.
   - Click **Save Profile**. Profile data is saved to `data/profile.json`.
3. **Medications**:
   - Navigate to **Medications**.
   - Click **Add Medication**: Name `Albuterol Inhaler`, Strength `90 mcg`, Dosage `2 puffs`, Route `Inhalation`, Active Ingredients `Albuterol Sulfate`.
   - Click **Save Medication**. The Safety Engine validates the entry and saves it to `data/medications.json`.
   - *Duplicate Protection Demo*: Try adding the exact same medication again. Notice the red conflict banner: **409 Exact duplicate blocked**.
   - *Allergy Warning Demo*: Add `Amoxicillin` with active ingredient `Penicillin`. Notice the Safety Engine accepts the record but flags a prominent **Allergy Warning** badge on the medication card.
4. **Care Episodes**:
   - Navigate to **Care Episodes**.
   - Click **Add Episode**: Title `Annual Asthma Review`, Category `Check-up`, Status `Ongoing`, Date `Today`, Symptoms `Occasional exercise-induced shortness of breath`.
   - Click **Save Episode**. Saved to `data/episodes.json`.
5. **Documents (RAG Ingestion)**:
   - Navigate to **Documents**.
   - Click to upload a medical PDF (e.g. clinic summary or discharge document under 10 MB).
   - PyMuPDF extracts text page-by-page, generates Sentence-Transformer embeddings, and indexes chunks into persistent ChromaDB storage (`data/chroma/`).
   - Notice the document appears with filename, file size, page count, and status `indexed`.
6. **Health Copilot (Grounding & Citations)**:
   - Navigate to **Health Copilot**.
   - Ask: *"What medications am I taking and what does my uploaded report say?"*
   - MedBuddy gathers context from the persistent profile, episodes, and retrieved ChromaDB PDF chunks.
   - The response includes the grounded answer, context source badges, and **Document Citations** displaying the exact filename and page number.
7. **Emergency Short-Circuit Demo**:
   - In Health Copilot, type: *"I have severe crushing chest pain and difficulty breathing."*
   - The Safety Engine intercepts the message before any LLM call.
   - An urgent red alert banner is displayed immediately advising emergency medical care, bypassing Gemini.
8. **Persistence Across Restart**:
   - Stop the backend server (`Ctrl+C` in Terminal 1).
   - Restart the server with `python -m uvicorn backend.main:app --port 8000`.
   - Refresh `http://localhost:5173`. All profile details, medications, episodes, and indexed documents persist intact.

---

## 8. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status |
| `GET` | `/profile` | Get stored health profile |
| `PUT` | `/profile` | Upsert health profile (allergies, conditions, emergency contact) |
| `GET` | `/medications` | List all medications |
| `POST` | `/medications` | Add medication with safety check & duplicate rejection |
| `GET` | `/medications/{id}` | Get medication by ID |
| `PUT` | `/medications/{id}` | Update medication with safety check |
| `DELETE` | `/medications/{id}` | Delete medication |
| `GET` | `/episodes` | List care episodes |
| `POST` | `/episodes` | Create care episode |
| `GET` | `/episodes/{id}` | Get care episode by ID |
| `PUT` | `/episodes/{id}` | Update care episode |
| `DELETE` | `/episodes/{id}` | Delete care episode |
| `GET` | `/documents` | List uploaded indexed documents |
| `POST` | `/documents/upload` | Upload & index PDF (multipart form-data) |
| `DELETE` | `/documents/{id}` | Delete document, PDF file & ChromaDB chunks |
| `POST` | `/chat` | Health Copilot query with RAG context & safety check |

---

## 9. Known Limitations

- **Authentication**: Single-user demo environment. Real multi-tenant authentication (OAuth/JWT) is simulated with a prototype entry gate.
- **Clinical Scope**: MedBuddy is a personal health context and record organization tool, not a certified medical diagnostic device.
- **Safety Engine Scope**: Detects configured emergency keywords, exact medication duplicates, ingredient overlaps, and documented allergy conflicts; does not replace professional clinical pharmacology databases.

---

## 10. Safety Disclaimer

> [!IMPORTANT]
> **Not Medical Advice**: MedBuddy is intended for personal health information organization and patient communication support only. It does not diagnose, prescribe, or provide clinical medical decisions. In any life-threatening emergency, call your local emergency service (911, 112) immediately.
