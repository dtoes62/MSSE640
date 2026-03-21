# Triangle Analyzer

A full-stack web application that accepts three side lengths, validates whether
they form a triangle, and classifies the triangle type (equilateral, isosceles,
or scalene). Invalid inputs are handled via custom exceptions. Includes animated
UI built with React and a REST API backend built with FastAPI.

---

# Triangle Analyzer UI

![Triangle Analyzer UI](docs/week1TriangleApp.png)

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.10+ | `python3 --version` |
| pip | any | `pip3 --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/dtoes62/MSSE640.git
cd MSSE640
```

### 2. Install backend dependencies

```bash
cd backend
pip3 install fastapi uvicorn httpx pytest
```

### 3. Install frontend dependencies

```bash
cd ../frontend
npm install
```

---

## Running the App

From the project root, the easiest way is the included startup script:

```bash
bash start.sh
```

This starts both servers simultaneously:

| Server | URL |
|--------|-----|
| React frontend | http://localhost:5173 |
| FastAPI backend | http://localhost:8000 |
| API docs (auto-generated) | http://localhost:8000/docs |

Press **Ctrl+C** to stop both servers.

### Running servers manually (alternative)

**Backend** (from the `backend/` directory):
```bash
python3 -m uvicorn main:app --reload --port 8000
```

**Frontend** (from the `frontend/` directory):
```bash
npm run dev
```

---

## Running the Tests

From the `backend/` directory:

```bash
# All tests (unit + integration)
python3 -m pytest tests/ -v

# Unit tests only (pure triangle logic)
python3 -m pytest tests/test_triangle.py -v

# Integration tests only (HTTP layer)
python3 -m pytest tests/test_api.py -v
```

---

## Project Structure

```
Week1Project/
├── backend/
│   ├── main.py           # FastAPI app and routes
│   ├── triangle.py       # Triangle validation and classification logic
│   ├── exceptions.py     # Custom exception classes
│   └── tests/
│       ├── test_triangle.py  # Unit tests (pure logic)
│       └── test_api.py       # Integration tests (HTTP endpoints)
├── frontend/
│   └── src/
│       ├── App.jsx           # Root component, debounced API calls
│       ├── api.js            # Fetch wrapper
│       ├── constants.js      # Shared colors and canvas constants
│       ├── hooks/
│       │   └── useTriangleGeometry.js  # Law of cosines computation
│       └── components/
│           ├── TriangleForm.jsx        # Input form
│           ├── TriangleAnimation.jsx   # Animation orchestrator
│           ├── TriangleSide.jsx        # Animated steel I-beam sides
│           ├── DustParticles.jsx       # Particle burst effect
│           ├── LiquidMetal.jsx         # Molten pool effect
│           └── TriangleLegend.jsx      # Triangle type color key
├── start.sh          # Starts both servers with one command
└── README.md
```

---

## Notes for WSL (Windows Subsystem for Linux) Users

The Vite dev server is configured to use filesystem polling so that hot-reload
works correctly on the Windows filesystem (`/mnt/c/...`). This is already set
in `frontend/vite.config.js` and requires no extra steps.
