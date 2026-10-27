# KrishiSetu — full-stack source

KrishiSetu is a React/Vite frontend with a FastAPI backend and PostgreSQL persistence. This update adds crop- and region-based communities, an official mandi-price sync path, a seeded government-scheme directory, and an official PIB RSS news importer. It does not generate fake market prices or fake news.

## Requirements
- Python 3.12+ (Python 3.14 may work but dependency compatibility should be checked in your environment)
- Node.js 20+ and npm
- PostgreSQL
- Optional data.gov.in API key for official mandi-price sync

## Local setup (Windows PowerShell)
From the extracted project root:

```powershell
# Existing project: preserve your working .env; do not overwrite it.
# If setting up from scratch, copy .env.example to .env and set DB credentials + SECRET_KEY.
py -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:PYTHONPATH = "$PWD\backend"
.\backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell window:

```powershell
cd .\frontend
npm ci
npm run dev
```

The frontend is configured to start at `http://127.0.0.1:5174`. The Vite proxy forwards `/api` requests to the backend at `http://127.0.0.1:8000`; keep both terminal windows open.

## API URLs
- Health: `http://127.0.0.1:8000/health`
- Swagger docs: `http://127.0.0.1:8000/api/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/api/openapi.json`
- API base: `/api/v1`

## Community
- `GET /api/v1/content/community/groups` lists crop and region communities.
- `POST /api/v1/content/community/groups` creates a community (login required).
- `POST /api/v1/content/community/groups/{id}/join` joins a community (login required).
- `GET/POST /api/v1/content/community/posts` lists and publishes PostgreSQL-backed posts; posts can be scoped to a community.
- The migration creates starter crop communities for Cotton, Papaya, Banana, Jowar, Wheat, Bajra, Fruits, and Vegetables. Users can create custom State/District/Taluka/Village groups.

## Market prices
- The price page reads sourced records from PostgreSQL and filters by crop, district, state, and optional mandi/market name.
- Official source: data.gov.in Agmarknet resource `9ef84268-d588-465a-a308-a864a43d0070`.
- Set `DATA_GOV_IN_API_KEY` in `.env` to a valid key from data.gov.in. An admin can manually call `POST /api/v1/market-prices/sync`. When the key is configured at backend startup, a background sync runs on startup and then every 24 hours.
- Without a key or when the official endpoint fails, the app shows a clear error/empty state and does not generate demo prices.

## Schemes
- Migration seeds 12 farmer-focused scheme records with official source links and document guidance: PM-KISAN, PMFBY, KCC, PMKSY, Soil Health Card, e-NAM, PM-KUSUM, Agriculture Infrastructure Fund, RKVY, PM-AASHA, SMAM, and NBHM.
- Apply Now opens the scheme's official portal or official information page. Some programmes are state/component-based rather than a universal individual application form; the UI says to verify current eligibility and document checklists on the linked official source.

## News
- `GET /api/v1/content/resources/news?refresh=true` fetches the official PIB Press Releases RSS feed, filters agriculture-related items, and saves new source-linked items in PostgreSQL. It refreshes at most once every 30 minutes per backend process and retains saved records if the feed is temporarily unavailable.

## Important limitations / validation
- A data.gov.in API key and network access are required for live mandi-price sync. The API key is intentionally not included in this ZIP.
- Government scheme details and required documents may change; users must verify the current official portal and state-specific notices before applying.
- Run `npm ci`, `npm run build`, the Alembic migration and endpoint smoke tests on the target Windows machine before production deployment. Package installation/build could not be completed in this packaging environment because npm installation timed out.
