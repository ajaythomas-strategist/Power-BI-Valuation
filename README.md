# Power BI Answer Evaluator
**Automated Power BI Project Assessment Platform**

A production-quality web application built for Power BI trainers and academic evaluators to automatically assess student Power BI projects (`.pbip`) against a Question Paper and Answer Key with 100% deterministic, explainable, rule-based scoring.

---

## Key Features

- **Multi-Format PBIP Analysis**:
  - Semantic Models in both Tabular JSON (`model.bim`) and TMDL (`definition/tables/*.tmdl`, `relationships.tmdl`).
  - Report pages and visuals in both classic `report.json` and enhanced PBIR (`definition/pages/*/page.json` & `visuals/*/visual.json`).
  - Tables, columns, calculated columns, measures, relationships (cardinalities, cross-filters), filters, slicers, and visuals.
- **DAX AST & Normalization Engine**:
  - Semantic tokenization and comparison.
  - Strips comments, whitespace, and table qualifier variations (`'Sales'[Amount]` vs `[Amount]`).
  - Evaluates mathematical and function equivalences (`SUM`, `CALCULATE`, `DIVIDE`, `SUMX`, `AVERAGE`).
- **Flexible Answer Key & Rule Editor**:
  - Upload JSON, YAML, CSV, or formatted text Answer Keys.
  - Interactive **Rule Review & Edit** step (Screen 3) allowing trainers to adjust criteria, accepted variations, and mark weights before evaluation.
- **Automated Batch Processing & Exception Isolation**:
  - Automatically identifies student Register Numbers directly from immediate subfolder names (e.g., `23001`, `23002`).
  - Tolerates missing submissions, corrupted files, and unsupported structures without halting the batch.
- **Professional 4-Sheet Excel Exporter (`openpyxl`)**:
  - **Sheet 1 — Summary**: Register No, Total Marks, Max Marks, Percentage, Questions Breakdown, Status Tag, Class Averages.
  - **Sheet 2 — Question-wise Evaluation**: Granular student implementation vs expected requirements with awarded sub-marks and explainable remarks.
  - **Sheet 3 — Exceptions**: Diagnostic logs of missing or unparsable submissions.
  - **Sheet 4 — Evaluation Rules**: Complete audit record of the parsed Answer Key criteria.
- **Strict White Premium Theme**:
  - Designed specifically for education & enterprise training environments with high contrast, clear visual hierarchy, and zero dark-mode distraction.
- **Zero Permanent Storage**:
  - Student projects and reports are processed in ephemeral memory and cleaned up immediately after evaluation.

---

## System Architecture

```
Power BI Answer Evaluator
├── frontend/                     # Next.js 15 App (React 19, TypeScript, Tailwind CSS)
│   ├── src/
│   │   ├── app/                  # App router pages & layouts (White Premium Theme)
│   │   ├── components/           # 8-step guided evaluation components
│   │   ├── lib/api.ts            # FastAPI client connector
│   │   └── types/                # TypeScript data interfaces
│   └── package.json
│
├── backend/                      # Python 3 + FastAPI Backend
│   ├── app/
│   │   ├── main.py               # Application entry point & CORS
│   │   ├── models/schemas.py     # Pydantic data schemas
│   │   ├── parsers/
│   │   │   ├── pbip_parser.py    # PBIP, TMDL, BIM, PBIR parser
│   │   │   ├── dax_analyzer.py   # DAX AST normalizer & equivalence checker
│   │   │   └── answer_key_parser.py # Answer key to rule-set converter
│   │   ├── evaluator/
│   │   │   └── engine.py         # Deterministic rule-matching engine
│   │   ├── exporters/
│   │   │   └── excel_exporter.py # openpyxl 4-sheet styled report generator
│   │   ├── services/
│   │   │   ├── batch_scanner.py  # Student folder & Register No detector
│   │   │   └── cleanup_service.py # Ephemeral session storage manager
│   │   └── api/routes.py         # REST endpoints
│   ├── tests/                    # Pytest test suite (11 test suites)
│   └── requirements.txt
│
└── fixtures/                     # Sample datasets for 1-click demo & testing
    └── sample_data_generator.py  # Realistic PBIP fixtures (5 student scenarios)
```

---

## 8-Step Guided Workflow

1. **Step 1: Upload Question Paper** (PDF, Word, Markdown, or Text preview)
2. **Step 2: Upload Answer Key** (JSON, YAML, CSV, or Text)
3. **Step 3: Review & Edit Evaluation Rules** (Interactive card editor with sub-criteria and accepted variations)
4. **Step 4: Select Student Main Folder / ZIP Archive** (Hierarchy verification)
5. **Step 5: Scan Submissions** (Register number detection & integrity verification)
6. **Step 6: Evaluation Execution & Progress** (Live animated progress bar & student status ticker)
7. **Step 7: Consolidated Results** (KPI cards, sortable table, and student question-by-question modal)
8. **Step 8: Export Excel** (Download `.xlsx` report & clean session storage)

---

## Quick Start & Local Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+

### 1. Backend Setup
```bash
# Navigate to project root
cd "backend"

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend test suite
PYTHONPATH=. pytest tests -v

# Start FastAPI backend server (Runs on http://localhost:8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
# Open a new terminal and navigate to frontend
cd "frontend"

# Install dependencies
npm install

# Start Next.js development server (Runs on http://localhost:3000)
npm run dev
```

Visit **http://localhost:3000** in your browser and click **"Instant Sample Demo"** to run an immediate end-to-end evaluation!

---

## Deployment Guide (Vercel + Backend)

### Frontend on Vercel
1. Connect this repository to **Vercel**.
2. Set Root Directory to `frontend`.
3. Set the Environment Variable:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-service.railway.app
   ```
4. Deploy!

### Backend on Cloud Run / Railway / Render
1. Deploy `backend/` as a Docker container or Python service.
2. Ensure Python 3.10+ and standard memory allocation (512MB–1GB).
3. The backend does not require any external database or persistent disk storage.

---

## Known Limitations & Phase 2 Roadmap

### PBIP Format Nuances (Phase 1 Status)
- Phase 1 fully parses:
  - Standard Microsoft Power BI Desktop PBIP projects
  - Tabular Object Model (`model.bim`)
  - TMDL definitions (`definition/tables/*.tmdl`, `relationships.tmdl`)
  - Standard Report Visuals (`report.json` and PBIR `definition/pages/*/page.json` + `visuals/*/visual.json`)
- Highly customized third-party custom visuals from AppSource with obfuscated internal configurations may fall back to visual-type and query-ref validation.

### Phase 2 Expansion (Deferred for Future)
- Trainer authentication & multi-tenant accounts
- Long-term institutional historical analytics
- Question paper bank and reusable rubric templates
- Direct LMS (Canvas / Moodle / Blackboard) grade sync
