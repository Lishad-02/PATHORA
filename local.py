"""Run the full site (pages and both agent APIs) on http://127.0.0.1:8000."""

import uvicorn
from fastapi.staticfiles import StaticFiles

from app import ROOT, app

app.mount("/", StaticFiles(directory=ROOT / "public", html=True), name="site")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
