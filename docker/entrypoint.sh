#!/usr/bin/env sh
set -e

# Ensure directories + database schema exist before serving.
python - <<'PY'
import asyncio
from downtube.config import settings
from downtube.db.session import init_db

settings.ensure_dirs()
asyncio.run(init_db())
PY

exec uvicorn downtube.main:app --host 0.0.0.0 --port 9876
