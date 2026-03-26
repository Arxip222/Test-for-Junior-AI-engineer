from __future__ import annotations

import csv
from pathlib import Path


def load_financial_data(csv_path: str | Path) -> list[dict[str, float]]:
    """Load financial data from CSV, trying multiple encodings."""
    rows: list[dict[str, float]] = []
    encodings = ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "cp1251", "cp1252"]
    last_exc: Exception | None = None

    for enc in encodings:
        try:
            with open(csv_path, "r", encoding=enc) as f:
                reader = csv.DictReader(f)
                rows.clear()
                for r in reader:
                    r_norm = {str(k).strip(): v for k, v in r.items() if k is not None}
                    rows.append(
                        {
                            "year": float(r_norm["year"]),
                            "revenue": float(r_norm["revenue"]),
                            "cogs": float(r_norm["cogs"]),
                            "operating_expenses": float(r_norm["operating_expenses"]),
                            "net_income": float(r_norm["net_income"]),
                        }
                    )
            if rows:
                break
        except (UnicodeDecodeError, KeyError) as e:
            last_exc = e
            rows.clear()

    if not rows and last_exc is not None:
        raise last_exc

    rows.sort(key=lambda x: x["year"])
    return rows
