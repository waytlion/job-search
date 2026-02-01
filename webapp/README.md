# Job Search Web Application

A full-stack web application for managing and viewing job search data scraped by the job-search pipeline.

## Features

- **Dashboard**: Overview statistics, charts, and top locations/companies
- **Jobs List**: Paginated, filterable, sortable job listings
- **Job Details**: Modal view with full job description and user notes
- **Status Tracking**: Mark jobs as interested, applied, not interested, etc.
- **Score Filtering**: Filter by total score, individual score components
- **Settings**: Adjust scoring weights and recalculate all scores

## Architecture

```
webapp/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── main.py        # FastAPI entry point
│   │   ├── database/      # SQLite connection
│   │   ├── models/        # Pydantic models
│   │   └── routes/        # API endpoints
│   └── requirements.txt
│
└── frontend/         # Next.js React frontend
    ├── src/
    │   ├── app/           # Next.js pages
    │   ├── components/    # React components
    │   └── lib/           # API client, types
    └── package.json
```

## Quick Start

### Backend (FastAPI)

```bash
cd webapp/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Frontend (Next.js)

```bash
cd webapp/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

## API Endpoints

### Jobs
- `GET /api/jobs` - List jobs (paginated, with filters)
- `GET /api/jobs/{id}` - Get single job details
- `PATCH /api/jobs/{id}` - Update job status/notes
- `POST /api/jobs/{id}/status/{status}` - Quick status update

### Stats
- `GET /api/stats` - Dashboard statistics

### Config
- `GET /api/config` - Get scoring configuration
- `PUT /api/config` - Update scoring weights

### Filters
- `GET /api/filters/options` - Get available filter values

### Sync
- `POST /api/sync` - Trigger data sync
- `GET /api/sync/history` - Get sync history

## Database

The webapp uses the existing `jobs.db` SQLite database from the scraper.
On first run, it adds three new columns:
- `user_status` - Track your interaction with each job
- `user_notes` - Personal notes for each job
- `user_updated_at` - Timestamp of last user update

## User Statuses

- `not_viewed` - Haven't looked at it yet
- `interested` - Looks promising
- `applied` - Application submitted
- `not_interested` - Not a fit
- `archived` - Done reviewing

## Development

### Backend
```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest
```

### Frontend
```bash
# Development
npm run dev

# Build for production
npm run build

# Type checking
npm run lint
```

## Production Deployment

### Backend
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Frontend
```bash
npm run build
npm start
```

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Optional: For GitHub sync feature
GITHUB_TOKEN=your_github_token
GITHUB_REPO=username/repo
```
