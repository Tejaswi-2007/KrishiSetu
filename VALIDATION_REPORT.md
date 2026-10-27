# KrishiSetu feature update and validation report

## Changes in this package
- Added PostgreSQL-backed crop and region communities, community membership, community-specific posts, and search.
- Added starter crop communities for Cotton, Papaya, Banana, Jowar, Wheat, Bajra, Fruits, and Vegetables.
- Added custom region community creation with State, District, Taluka, and Village fields; state can be selected from suggestions or typed manually.
- Added 12 source-linked farmer scheme records to the Alembic migration, including official source/apply links and scheme-specific document guidance where known.
- Connected the News page to the official PIB Press Releases RSS feed. Agriculture-related items are filtered, deduplicated, and stored in PostgreSQL; saved news remains available if the feed is temporarily unavailable.
- Refactored data.gov.in Agmarknet market-price sync into a reusable service. The admin endpoint remains available, and a background sync runs on startup and every 24 hours when `DATA_GOV_IN_API_KEY` is configured.
- Added State filtering to the market-price UI and improved empty/error messaging to avoid fake data.
- Updated project README with new API endpoints, source behavior, migration instructions, and external-key requirements.

## Validation performed in this packaging environment
- Python `compileall` passed for `backend/app` and `backend/alembic/versions`.
- The new Alembic migration parsed successfully.
- A full FastAPI import/startup test could not complete in this environment because runtime dependencies such as `python-jose` and `psycopg` are not installed here.
- Frontend `npm ci` timed out in this environment; Vite build/type-check could not be completed here.
- PostgreSQL migration execution, PIB RSS retrieval, and live data.gov.in sync were not run here.

## Required on the target Windows machine
1. Preserve the existing `.env` and database credentials.
2. Run `alembic upgrade head` to apply migration `5d2a91c7b840` after the already-applied `41c9a0b7d3e2` revision.
3. For live mandi prices, set a valid `DATA_GOV_IN_API_KEY` in `.env` and restart the backend. Without the key, the app intentionally will not invent prices.
4. Run `npm ci` and `npm run build` in `frontend` and test the flows against the local PostgreSQL database.

## Data integrity notes
- Scheme records are a curated starter directory and link to official portals. Eligibility and document requirements can vary by state, season, and scheme; users should confirm current details on the linked portal.
- News entries are linked to original PIB articles and are not generated/fabricated.
- No fake market prices are seeded.
