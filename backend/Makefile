SHELL := /bin/sh

.PHONY: openapi

openapi:
	python - <<'PY'

from app.main import app
from pathlib import Path
import json

schema = app.openapi()
out = Path(__file__).parent.parent / "docs" / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
print(f"OpenAPI schema written to {out}")

PY

