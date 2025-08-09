from __future__ import annotations
from datetime import datetime
from pathlib import Path
import csv
from typing import Optional

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def write_oplog(platform: str, op: str, url: Optional[str] = None, content: Optional[str] = None,
                 ok: bool = True, error: Optional[str] = None, ms: Optional[int] = None) -> None:
    """Append one operation record to CSV (logs/ops-YYYYMMDD.csv). Creates header if file not exists."""
    day = datetime.now().strftime("%Y%m%d")
    path = LOG_DIR / f"ops-{day}.csv"
    is_new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["time", "platform", "op", "url", "content", "ok", "error", "ms"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"), platform, op, url or "", content or "",
            "1" if ok else "0", error or "", ms if ms is not None else ""
        ])

