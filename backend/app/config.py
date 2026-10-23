import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
MARKET_TZ = "Europe/London"

# ASSUMPTION (unverified): day-ahead gate closure 09:20 UK local time on D-1.
# Configurable because the client's real cutoff may differ.
DEFAULT_CUTOFF = os.getenv("DEFAULT_CUTOFF", "09:20")
