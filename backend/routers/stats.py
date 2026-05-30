from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Query

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from news_analyser.stats import (
    _load_dataframe,
    top_techniques,
    top_domains,
    top_stroemungen,
    orwell_distribution,
    bernays_distribution,
    dunning_kruger_distribution,
    domain_averages,
    sentiment_distribution,
    daily_verlauf,
)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/verlauf")
def get_verlauf(domain: str | None = Query(None)) -> list[dict]:
    df = _load_dataframe()
    if df.empty:
        return []
    return daily_verlauf(df, domain=domain)


@router.get("")
def get_stats() -> dict:
    df = _load_dataframe()
    if df.empty:
        return {"total_articles": 0}

    dom_df = domain_averages(df)
    dom_list = []
    for domain, row in dom_df.iterrows():
        entry = {
            "domain":      domain,
            "artikel":     int(row["artikel"]),
            "orwell_avg":  round(float(row["orwell_avg"]), 3),
            "bernays_avg": round(float(row["bernays_avg"]), 3),
        }
        if "dk_avg" in row:
            entry["dk_avg"] = round(float(row["dk_avg"]), 3)
        dom_list.append(entry)

    dk = dunning_kruger_distribution(df)

    stroemungen = top_stroemungen(df)
    stroemungen_dict = stroemungen.to_dict() if not stroemungen.empty else {}

    return {
        "total_articles":       len(df),
        "top_techniques":       top_techniques(df, 10).to_dict(),
        "top_domains":          top_domains(df, 10).to_dict(),
        "top_stroemungen":      stroemungen_dict,
        "orwell_distribution":  orwell_distribution(df),
        "bernays_distribution": bernays_distribution(df),
        "dk_distribution":      dk if dk else None,
        "domain_averages":      dom_list,
        "sentiment_distribution": sentiment_distribution(df).to_dict(),
    }
