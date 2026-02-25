# CLAUDE.md — AI Document Reader (ai-doc)

## Project Overview

A full-stack web application for uploading bank statement PDFs, extracting transaction data via OCR, and exporting results as Excel files. The project is a monorepo with a React frontend and a Python Flask backend.

**Supported banks:** Palus Sahakari Bank, HDFC Bank (extensible via parser plugins).

## Repository Structure

```
ai-doc/
├── ai-doc-frontend/          # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx           # Root router component
│   │   ├── main.jsx          # Entry point
│   │   ├── auth/             # AuthProvider (Context API), PrivateRoute
│   │   ├── modules/
│   │   │   ├── Common/       # Header, Footer
│   │   │   ├── Login/        # Login, Register components + useLogin hook
│   │   │   └── Document/     # MainPage (upload, list, download)
│   │   └── styles/
│   │       └── theme.js      # MUI dark theme config
│   ├── package.json
│   ├── vite.config.js
│   ├── eslint.config.js
│   └── tsconfig.json
│
├── ai-doc-backend/
│   └── parsers_python/       # Flask backend
│       ├── app.py            # Main Flask app (routes, auth, upload handling)
│       ├── models.py         # User model (MongoDB)
│       ├── parsers/
│       │   ├── base_parser.py    # Abstract base parser class
│       │   ├── palus_parser.py   # Palus Sahakari Bank parser
│       │   ├── hdfc_parser.py    # HDFC Bank parser
│       │   └── factory.py        # ParserFactory (auto-detects bank format)
│       ├── utils/
│       │   ├── pdf_extractor.py  # PDF text extraction + OCR (Tesseract)
│       │   └── excel_exporter.py # Excel file generation (openpyxl)
│       ├── requirements.txt
│       ├── .env.example
│       ├── test_parser.py        # Parser test script
│       ├── start-python.sh       # Linux/Mac startup
│       └── start-python.bat      # Windows startup
│
└── .gitignore
```

## Tech Stack

### Frontend
- **React 19** with JSX (not TSX — source files are `.jsx` despite TypeScript config presence)
- **Vite** (via rolldown-vite) for bundling and dev server
- **Material-UI 7** (`@mui/material`) with Emotion for styling
- **Redux Toolkit** for state management
- **React Router DOM 7** for routing
- **Axios** for HTTP requests
- **ESLint 9** (flat config) with React hooks + React Refresh plugins

### Backend
- **Python 3.8+ / Flask 3.0**
- **MongoDB** via Flask-PyMongo / pymongo
- **Flask-Login + Flask-Bcrypt** for authentication
- **pdfplumber / PyPDF2 / pdf2image** for PDF processing
- **pytesseract** for OCR (requires system Tesseract installation)
- **openpyxl** for Excel export
- **Flask-CORS** for cross-origin requests

## Development Setup

### Frontend

```bash
cd ai-doc-frontend
npm install
npm run dev          # Starts Vite dev server on port 5173
```

### Backend

```bash
cd ai-doc-backend/parsers_python
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # Edit with real MongoDB URI and secret key
python app.py          # Starts Flask on port 5001
```

**System dependency:** Tesseract OCR must be installed on the host. Set `TESSERACT_PATH` in `.env` if not on the default system PATH.

## Available Commands

### Frontend (`ai-doc-frontend/`)
| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server (port 5173) |
| `npm run build` | Production build to `dist/` |
| `npm run lint` | Run ESLint across the project |
| `npm run preview` | Preview production build locally |

### Backend (`ai-doc-backend/parsers_python/`)
| Command | Description |
|---------|-------------|
| `python app.py` | Start Flask server (port 5001) |
| `python -m pytest test_parser.py` | Run parser tests |
| `bash start-python.sh` | Startup script (Linux/Mac) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login |
| `POST` | `/auth/logout` | Logout |
| `GET` | `/api/me` | Get current authenticated user |
| `POST` | `/upload` | Upload PDF for processing |
| `GET` | `/api/documents` | List user's documents |
| `GET` | `/download/<filename>` | Download processed file |
| `POST` | `/parse` | Direct OCR text parsing |
| `POST` | `/parse-json` | Parse to structured JSON |

## Architecture & Key Patterns

- **Monorepo** — frontend and backend in the same repo, developed/deployed independently.
- **REST API** — frontend communicates with backend via HTTP with credentials-included CORS.
- **Factory Pattern** — `ParserFactory` auto-detects the bank from extracted text and routes to the correct parser.
- **Plugin/Strategy Pattern** — new bank parsers extend `BaseParser` and register in the factory.
- **Context API** — `AuthProvider` manages auth state; `PrivateRoute` guards protected pages.
- **Feature-based module structure** — frontend `src/modules/` organized by feature (Login, Document, Common).

## Code Conventions

### Frontend
- Source files use `.jsx` extension (JavaScript + JSX), not `.tsx`.
- ESLint flat config format (`eslint.config.js`), targeting `**/*.{js,jsx}`.
- Unused variables starting with uppercase or underscore are allowed (`varsIgnorePattern: '^[A-Z_]'`).
- TypeScript config exists (`tsconfig.json` with strict mode) but source is written as JS/JSX with `allowJs: true`.
- Dark theme is the default (see `styles/theme.js`).
- Components use Material-UI's `sx` prop and `Box`/`Grid`/`Paper` layout primitives.

### Backend
- Flask app in a single `app.py` file containing all routes and middleware.
- Python naming: snake_case for functions/variables, PascalCase for classes.
- Parsers follow an inheritance hierarchy: `BaseParser` -> specific bank parsers.
- Environment configuration via `.env` file (loaded with python-dotenv).
- File uploads stored in `UPLOAD_FOLDER` directory with timestamp-based naming.

## Environment Variables

### Backend (`.env`)
| Variable | Purpose |
|----------|---------|
| `FLASK_DEBUG` | Enable debug mode |
| `FLASK_ENV` | Environment (development/production) |
| `UPLOAD_FOLDER` | Directory for uploaded files |
| `MAX_FILE_SIZE` | Max upload size in bytes (default 50MB) |
| `MONGODB_URI` | MongoDB connection string |
| `DB_NAME` | MongoDB database name |
| `SECRET_KEY` | Flask session secret key |
| `TESSERACT_PATH` | Path to Tesseract OCR binary |
| `FLASK_HOST` | Server host (default 0.0.0.0) |
| `FLASK_PORT` | Server port (default 5001) |

### Frontend
The frontend uses `VITE_API_BASE` (or similar) env variable to point to the backend URL. The dev default is `http://localhost:5001`.

## Adding a New Bank Parser

1. Create `ai-doc-backend/parsers_python/parsers/<bank>_parser.py`.
2. Extend `BaseParser` and implement the required parsing methods.
3. Register the new parser in `parsers/factory.py` with appropriate bank-detection keywords.
4. Test with `python -m pytest test_parser.py`.

## Important Notes

- **No CI/CD pipeline** is configured yet. Linting and tests must be run manually.
- **No Docker** setup exists. Both services run directly on the host.
- **MongoDB** is required — the backend will not start without a valid connection string.
- **Tesseract OCR** is a system-level dependency required for PDF text extraction.
- **Never commit `.env` files** — they contain secrets. Use `.env.example` as a template.
- **CORS** is configured to allow the frontend origin with credentials; update if deploying to different domains.
