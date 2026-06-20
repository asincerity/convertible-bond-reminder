from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class ExperimentTracker:
    def __init__(self, base_dir: str = "experiments"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def start_run(self, name: str, config: Dict[str, Any]) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.base / f"{name}_{ts}"
        run_dir.mkdir(parents=True, exist_ok=True)
        with open(run_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return run_dir

    def log_metrics(self, run_dir: Path, metrics_obj) -> None:
        metrics = asdict(metrics_obj) if hasattr(metrics_obj, "__dataclass_fields__") else dict(metrics_obj)
        with open(run_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
