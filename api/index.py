import sys
from pathlib import Path

# Make backend/app importable (the data CSVs also live under backend/data).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402,F401