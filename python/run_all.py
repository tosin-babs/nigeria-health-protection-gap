"""
Reproduce every number in the paper, in order, from the raw CSVs.

    python python/run_all.py

Each stage writes its outputs to output/tables and output/figures and prints
the validation checks as it goes. The whole pipeline takes about ten minutes,
almost all of it in the robustness grid.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config


STAGES = [
    ("Build analysis files", "build_data"),
    ("RQ1  Catastrophic expenditure", "che"),
    ("RQ2a Cost models", "costmodels"),
    ("RQ2b Premium build-up", "premium"),
    ("RQ3  Pool solvency", "ruin"),
    ("RQ4  Coverage counterfactual", "counterfactual"),
    ("Robustness", "robustness"),
    ("Recall bounds and bootstrap", "bounds"),
    ("Figures", "exhibits"),
    ("Calculator payload", "export_tool_data"),
    ("Manuscript number check", "check_manuscript"),
    ("Submission documents", "make_manuscript"),
]


def record_parameters():
    """Freeze every analytic choice alongside the results."""
    params = {k: v for k, v in vars(config).items()
              if k.isupper() and not k.startswith("_")
              and isinstance(v, (int, float, str, tuple, list, dict, bool))}
    params = {k: (list(v) if isinstance(v, tuple) else v) for k, v in params.items()}
    params["_run_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    params["_numpy"] = np.__version__
    params["_pandas"] = pd.__version__
    (config.ROOT / "output" / "params_used.json").write_text(
        json.dumps(params, indent=2, default=str))
    return params


def main():
    print("=" * 78)
    print("Paper 2 - Nigeria health-protection gap and informal-sector pricing")
    print("=" * 78)
    record_parameters()

    timings = []
    for title, module in STAGES:
        print(f"\n{'-' * 78}\n{title}\n{'-' * 78}")
        t0 = time.time()
        mod = __import__(module)
        mod.main()
        dt = time.time() - t0
        timings.append({"stage": title, "seconds": round(dt, 1)})
        print(f"[{title}: {dt:.1f}s]")

    pd.DataFrame(timings).to_csv(config.ROOT / "output" / "run_timings.csv",
                                 index=False)
    print(f"\n{'=' * 78}")
    print(f"Done in {sum(t['seconds'] for t in timings):.0f}s. "
          f"Tables in {config.TABLES}, figures in {config.FIGURES}.")


if __name__ == "__main__":
    main()
