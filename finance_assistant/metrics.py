from __future__ import annotations

import json
from typing import Any


def safe_div(a: float, b: float) -> float | None:
    return None if b == 0 else a / b


def compute_metrics(rows: list[dict[str, float]]) -> dict[str, Any]:
    metrics_by_year: list[dict[str, Any]] = []
    revenue_growths: list[dict[str, Any]] = []
    prev_revenue: float | None = None

    for row in rows:
        year = int(row["year"])
        revenue = row["revenue"]
        cogs = row["cogs"]
        opex = row["operating_expenses"]
        net_income = row["net_income"]

        gross_profit = revenue - cogs
        operating_income = gross_profit - opex

        gross_margin = safe_div(gross_profit, revenue)
        operating_margin = safe_div(operating_income, revenue)
        net_margin = safe_div(net_income, revenue)

        revenue_growth = None
        if prev_revenue is not None and prev_revenue != 0:
            revenue_growth = (revenue - prev_revenue) / prev_revenue

        prev_revenue = revenue

        metrics_by_year.append(
            {
                "year": year,
                "revenue": revenue,
                "cogs": cogs,
                "operating_expenses": opex,
                "net_income": net_income,
                "gross_profit": gross_profit,
                "operating_income": operating_income,
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "net_margin": net_margin,
                "revenue_growth": revenue_growth,
            }
        )

        if revenue_growth is not None:
            revenue_growths.append({"year": year, "growth": revenue_growth})

    # Summary stats
    fastest = max(revenue_growths, key=lambda x: x["growth"]) if revenue_growths else None
    slowest = min(revenue_growths, key=lambda x: x["growth"]) if revenue_growths else None

    def minmax_stat(vals: list[tuple[int, float]]) -> dict[str, Any] | None:
        if not vals:
            return None
        mn = min(vals, key=lambda x: x[1])
        mx = max(vals, key=lambda x: x[1])
        avg = sum(v for _, v in vals) / len(vals)
        return {"min_year": mn[0], "min_value": mn[1], "max_year": mx[0], "max_value": mx[1], "avg_value": avg}

    op_vals = [(r["year"], r["operating_margin"]) for r in metrics_by_year if r["operating_margin"] is not None]
    net_vals = [(r["year"], r["net_margin"]) for r in metrics_by_year if r["net_margin"] is not None]
    gross_vals = [(r["year"], r["gross_margin"]) for r in metrics_by_year if r["gross_margin"] is not None]
    growth_vals = [(r["year"], r["revenue_growth"]) for r in metrics_by_year if r["revenue_growth"] is not None]

    first = metrics_by_year[0]
    last = metrics_by_year[-1]
    total_revenue_growth = safe_div(last["revenue"] - first["revenue"], first["revenue"])
    total_net_income_growth = safe_div(last["net_income"] - first["net_income"], first["net_income"])

    summary = {
        "years_covered": f"{first['year']}-{last['year']}",
        "total_years": len(metrics_by_year),
        "revenue_start": first["revenue"],
        "revenue_end": last["revenue"],
        "total_revenue_growth_percent": (total_revenue_growth or 0) * 100,
        "net_income_start": first["net_income"],
        "net_income_end": last["net_income"],
        "total_net_income_growth_percent": (total_net_income_growth or 0) * 100,
        "fastest_revenue_growth": None if fastest is None else {
            "year": fastest["year"], "growth_percent": fastest["growth"] * 100
        },
        "slowest_revenue_growth": None if slowest is None else {
            "year": slowest["year"], "growth_percent": slowest["growth"] * 100
        },
        "operating_margin_stats": minmax_stat(op_vals),
        "net_margin_stats": minmax_stat(net_vals),
        "gross_margin_stats": minmax_stat(gross_vals),
        "revenue_growth_stats": minmax_stat(growth_vals),
    }

    return {"metrics_by_year": metrics_by_year, "summary": summary}


def format_context(metrics: dict[str, Any]) -> str:
    """Serialize metrics as JSON context for the LLM."""
    ctx = {
        "summary": metrics["summary"],
        "metrics_by_year": [
            {
                "year": r["year"],
                "revenue": r["revenue"],
                "cogs": r["cogs"],
                "operating_expenses": r["operating_expenses"],
                "net_income": r["net_income"],
                "gross_profit": r["gross_profit"],
                "operating_income": r["operating_income"],
                "revenue_growth_pct": None if r["revenue_growth"] is None else round(r["revenue_growth"] * 100, 4),
                "gross_margin_pct": None if r["gross_margin"] is None else round(r["gross_margin"] * 100, 4),
                "operating_margin_pct": None if r["operating_margin"] is None else round(r["operating_margin"] * 100, 4),
                "net_margin_pct": None if r["net_margin"] is None else round(r["net_margin"] * 100, 4),
            }
            for r in metrics["metrics_by_year"]
        ],
    }
    return json.dumps(ctx, ensure_ascii=False, indent=2)
