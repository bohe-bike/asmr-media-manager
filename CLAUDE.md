# ASMR Media Manager

ASMR 媒体整理中心 - 面向 Plex/NAS 的 ASMR 专用媒体管理系统。

## Tech Stack

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue 3 + TypeScript + Vite + Element Plus + Pinia
- **Deployment**: Docker Compose

## Project Structure

```
asmr_media_manager/
├── backend/          # Python FastAPI backend
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   ├── core/     # Constants, exceptions
│   │   └── utils/    # Utility functions
│   └── requirements.txt
├── frontend/         # Vue 3 SPA
│   └── src/
│       ├── api/      # Axios API layer
│       ├── stores/   # Pinia stores
│       ├── views/    # Page components
│       └── types/    # TypeScript types
├── docker/           # Docker configs
├── config/           # App config (YAML)
└── docker-compose.yml
```

## Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Swagger UI: http://localhost:8080/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev server: http://localhost:5173 (proxies /api to backend)

### Docker

```bash
docker-compose up -d
```

App: http://localhost:3000

## Key API Endpoints

- `POST /api/v1/scan` - Start scan
- `GET /api/v1/media` - List media
- `GET /api/v1/media/{id}` - Media detail
- `PATCH /api/v1/media/{id}` - Update media
- `POST /api/v1/rename/preview` - Preview rename
- `POST /api/v1/rename/execute` - Execute rename
- `GET /api/v1/author-rules` - List author rules
- `POST /api/v1/author-rules` - Create author rule
- `GET /api/v1/tags` - List tags
- `GET /api/v1/settings` - Get settings
