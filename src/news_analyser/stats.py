"""
Statistik-Auswertung der gespeicherten Artikel-Analysen.

Verwendung:
    python run.py --stats
    python run.py --stats --top 10
"""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd
from chromadb.utils import embedding_functions

from .repositories.db_storage import _get_collection

CANONICAL_EMOTIONS = [
    "Angst",
    "Wut",
    "Empörung",
    "Trauer",
    "Hoffnung",
    "Stolz",
    "Ekel",
    "Überraschung",
    "Neutral",
]

_EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
)


def _parse_targets(raw: Any) -> list[dict]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return []
    return []


def _load_dataframe() -> pd.DataFrame:
    """Lädt alle gespeicherten Metadaten aus ChromaDB als DataFrame."""
    collection = _get_collection()
    result = collection.get(include=["metadatas"])

    if not result["metadatas"]:
        return pd.DataFrame()

    df = pd.DataFrame(result["metadatas"])
    df["technique_names"] = df["technique_names"].apply(json.loads)
    if "politische_stroemung" in df.columns:
        df["politische_stroemung"] = df["politische_stroemung"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else ["neutral"]
        )
    if "themenbereich" not in df.columns:
        df["themenbereich"] = "Sonstiges"
    if "manipulation_targets" in df.columns:
        df["manipulation_targets"] = df["manipulation_targets"].apply(_parse_targets)
    else:
        df["manipulation_targets"] = [[] for _ in range(len(df))]
    return df


def top_techniques(df: pd.DataFrame, n: int = 5) -> pd.Series:
    """Häufigste Manipulationstechniken über alle Artikel."""
    all_techniques = [t for row in df["technique_names"] for t in row]
    return pd.Series(Counter(all_techniques)).sort_values(ascending=False).head(n)


def orwell_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """Statistische Kennzahlen des Orwell-Index (ideologische Richtung)."""
    scores = df["orwell_index"].astype(float)
    return {
        "mean":               round(scores.mean(), 3),
        "median":             round(scores.median(), 3),
        "std":                round(scores.std(), 3),
        "min":                round(scores.min(), 3),
        "max":                round(scores.max(), 3),
        "links (<-0.2)":      int((scores < -0.2).sum()),
        "neutral (-0.2–0.2)": int(((scores >= -0.2) & (scores <= 0.2)).sum()),
        "rechts (>0.2)":      int((scores > 0.2).sum()),
    }


def bernays_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """Statistische Kennzahlen des Bernays Score (Manipulationsintensität, normalisiert)."""
    scores = df["bernays_score"].astype(float)
    return {
        "mean":   round(scores.mean(), 2),
        "median": round(scores.median(), 2),
        "max":    round(scores.max(), 2),
        "min":    round(scores.min(), 2),
    }


def dunning_kruger_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """Statistische Kennzahlen des Dunning-Kruger-Index (epistemische Überzeugheit, 0.0–1.0)."""
    if "dunning_kruger_index" not in df.columns:
        return {}
    scores = df["dunning_kruger_index"].astype(float)
    return {
        "mean":              round(scores.mean(), 3),
        "median":            round(scores.median(), 3),
        "max":               round(scores.max(), 3),
        "min":               round(scores.min(), 3),
        "bescheiden (<0.3)": int((scores < 0.3).sum()),
        "moderat (0.3–0.6)": int(((scores >= 0.3) & (scores <= 0.6)).sum()),
        "überzeugt (>0.6)":  int((scores > 0.6).sum()),
    }


def top_stroemungen(df: pd.DataFrame, n: int = 10) -> pd.Series:
    """Häufigste politische Strömungen über alle Artikel."""
    if "politische_stroemung" not in df.columns:
        return pd.Series(dtype=int)
    all_labels = [label for row in df["politische_stroemung"] for label in row]
    return pd.Series(Counter(all_labels)).sort_values(ascending=False).head(n)


def top_domains(df: pd.DataFrame, n: int = 5) -> pd.Series:
    """Domains mit den meisten analysierten Artikeln."""
    return df["domain"].value_counts().head(n)


def sentiment_distribution(df: pd.DataFrame) -> pd.Series:
    """Aggregiert intendierte Emotionen via Embedding-Nearest-Neighbor zu kanonischen Labels."""
    if "intended_sentiment" not in df.columns:
        return pd.Series(dtype=int)

    raw = [s for s in df["intended_sentiment"].dropna().tolist() if s]
    if not raw:
        return pd.Series(dtype=int)

    canonical_embs: list[list[float]] = _EMBED_FN(CANONICAL_EMOTIONS)

    unique_strings = list(set(raw))
    unique_embs: list[list[float]] = _EMBED_FN(unique_strings)

    def _nearest(emb: list[float]) -> str:
        sims = [
            float(np.dot(emb, c) / (np.linalg.norm(emb) * np.linalg.norm(c)))
            for c in canonical_embs
        ]
        return CANONICAL_EMOTIONS[int(np.argmax(sims))]

    string_to_label = {s: _nearest(e) for s, e in zip(unique_strings, unique_embs)}

    counts: dict[str, int] = {label: 0 for label in CANONICAL_EMOTIONS}
    for s in raw:
        counts[string_to_label[s]] += 1

    return pd.Series(counts).sort_values(ascending=False)


def domain_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Durchschnittliche Kennwerte (Orwell, Bernays, DK) pro Nachrichtenportal."""
    cols = ["orwell_index", "bernays_score"]
    if "dunning_kruger_index" in df.columns:
        cols.append("dunning_kruger_index")

    for col in cols:
        df[col] = df[col].astype(float)

    agg = (
        df.groupby("domain")[cols]
        .agg(["mean", "count"])
    )
    # Flatten multi-level columns
    agg.columns = ["_".join(c) for c in agg.columns]

    # Article count comes from any count column
    agg = agg.rename(columns={"orwell_index_count": "artikel"})
    # Drop redundant count columns
    for col in ["bernays_score_count", "dunning_kruger_index_count"]:
        if col in agg.columns:
            agg = agg.drop(columns=[col])

    agg = agg.rename(columns={
        "orwell_index_mean":         "orwell_avg",
        "bernays_score_mean":        "bernays_avg",
        "dunning_kruger_index_mean": "dk_avg",
    })

    return agg.sort_values("bernays_avg", ascending=False).round(3)


def entity_targeting(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Aggregiert Manipulations-Targets: welche Entität wird wie oft positiv/negativ dargestellt."""
    rows = []
    for _, article_row in df.iterrows():
        domain = article_row.get("domain", "")
        bernays = float(article_row.get("bernays_score", 0.0))
        for t in article_row["manipulation_targets"]:
            entity = t.get("entity", "").strip()
            direction = t.get("direction", "neutral")
            rolle = t.get("rolle", "Sonstiges")
            if entity:
                rows.append({
                    "entity":    entity,
                    "direction": direction,
                    "rolle":     rolle,
                    "domain":    domain,
                    "bernays":   bernays,
                })
    if not rows:
        return pd.DataFrame()

    tdf = pd.DataFrame(rows)
    agg = (
        tdf.groupby(["entity", "direction"])
        .agg(
            anzahl=("entity", "count"),
            bernays_avg=("bernays", "mean"),
            domains=("domain", lambda x: ", ".join(sorted(set(x)))),
        )
        .reset_index()
        .sort_values(["anzahl", "entity"], ascending=[False, True])
        .head(n)
        .round({"bernays_avg": 2})
    )
    return agg


def thema_bernays(df: pd.DataFrame) -> pd.DataFrame:
    """Durchschnittlicher Bernays Score und Orwell-Index pro Themenbereich."""
    if "themenbereich" not in df.columns:
        return pd.DataFrame()
    cols = ["bernays_score", "orwell_index"]
    for col in cols:
        df[col] = df[col].astype(float)
    agg = (
        df.groupby("themenbereich")[cols]
        .agg(["mean", "count"])
    )
    agg.columns = ["_".join(c) for c in agg.columns]
    agg = agg.rename(columns={
        "bernays_score_mean":  "bernays_avg",
        "bernays_score_count": "artikel",
        "orwell_index_mean":   "orwell_avg",
        "orwell_index_count":  "_drop",
    }).drop(columns=["_drop"], errors="ignore")
    return agg.sort_values("bernays_avg", ascending=False).round(3)


_DEPENDENCY_ENTITIES: dict[str, list[str]] = {
    # Geopolitisch
    "regierung":  ["bundesregierung", "olaf scholz", "scholz", "ampel", "koalition", "bundesminister", "bundesregier"],
    "usa":        ["usa", "nato", "washington", "biden", "trump", "pentagon", "weißes haus", "white house"],
    "eu":         ["eu", "europäische union", "brüssel", "von der leyen", "europäische kommission", "europarl"],
    "russland":   ["russland", "putin", "kreml", "moskau", "russian"],
    "china":      ["china", "xi jinping", "peking", "kpch", "volksrepublik"],
    # Parteien
    "spd":        ["spd", "sozialdemokraten", "sozialdemokrat", "pistorius", "heil", "esken", "klingbeil"],
    "cdu_csu":    ["cdu", "csu", "union", "merz", "söder", "unionsfraktion", "schwarze null"],
    "gruene":     ["grüne", "grünen", "bündnis 90", "habeck", "baerbock", "özdemir"],
    "fdp":        ["fdp", "freie demokraten", "liberale", "lindner", "wissing", "dürr"],
    "afd":        ["afd", "alternative für deutschland", "weidel", "chrupalla", "höcke"],
    "bsw":        ["bsw", "bündnis sahra wagenknecht", "wagenknecht"],
    "linke":      ["die linke", "linkspartei", "gysi", "bartsch", "pellmann"],
}

_DEPENDENCY_LABELS: dict[str, str] = {
    "regierung": "Regierungsfreundlich",
    "usa":       "US-freundlich",
    "eu":        "EU-freundlich",
    "russland":  "Russland-freundlich",
    "china":     "China-freundlich",
    "spd":       "SPD",
    "cdu_csu":   "CDU/CSU",
    "gruene":    "Grüne",
    "fdp":       "FDP",
    "afd":       "AfD",
    "bsw":       "BSW",
    "linke":     "Linke",
}


def trend_analysis(df: pd.DataFrame) -> dict:
    """Trend-Analyse: Domain-Trend-Cards, Themen-Heatmap, Domain-Vergleich wochenweise."""
    if df.empty:
        return {"trend_cards": [], "topic_heatmap": [], "domain_comparison": []}

    df = df.copy()
    df["date"] = pd.to_datetime(
        df["published_at"].where(df["published_at"].notna(), df.get("timestamp")),
        errors="coerce",
    ).dt.date
    df = df.dropna(subset=["date"])
    for col in ["orwell_index", "bernays_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    today = df["date"].max()
    cutoff_recent = today - pd.Timedelta(days=14)
    cutoff_prev   = today - pd.Timedelta(days=28)

    recent = df[df["date"] > cutoff_recent]
    prev   = df[(df["date"] > cutoff_prev) & (df["date"] <= cutoff_recent)]

    # --- 1. Trend-Cards pro Domain ---
    trend_cards = []
    for domain in df["domain"].unique():
        r = recent[recent["domain"] == domain]
        p = prev[prev["domain"] == domain]
        if len(r) < 2:
            continue
        card: dict = {"domain": domain, "artikel_recent": len(r)}
        for metric, label in [("orwell_index", "orwell"), ("bernays_score", "bernays")]:
            r_val = float(r[metric].median())
            p_val = float(p[metric].median()) if len(p) >= 2 else None
            delta = round(r_val - p_val, 3) if p_val is not None else None
            pct   = round((delta / p_val) * 100, 1) if (delta is not None and p_val and p_val != 0) else None
            card[label] = {"current": round(r_val, 3), "delta": delta, "pct": pct}
        trend_cards.append(card)
    trend_cards.sort(key=lambda x: -(x.get("orwell", {}).get("current") or 0))

    # --- 2. Themen-Heatmap (letzte 8 Wochen) ---
    cutoff_8w = today - pd.Timedelta(weeks=8)
    hm_df = df[df["date"] >= cutoff_8w].copy()
    hm_df["week"] = pd.to_datetime(hm_df["date"]).dt.strftime("%Y-W%W")
    if not hm_df.empty and "themenbereich" in hm_df.columns:
        hm = (
            hm_df.groupby(["themenbereich", "week"])["orwell_index"]
            .median()
            .round(3)
            .reset_index()
            .rename(columns={"orwell_index": "orwell"})
        )
        weeks_sorted = sorted(hm["week"].unique())
        topics = list(hm["themenbereich"].unique())
        heatmap_rows = []
        for topic in sorted(topics):
            cells = []
            for week in weeks_sorted:
                val = hm[(hm["themenbereich"] == topic) & (hm["week"] == week)]["orwell"]
                cells.append(float(val.iloc[0]) if len(val) else None)
            heatmap_rows.append({"topic": topic, "cells": cells})
        topic_heatmap = {"weeks": weeks_sorted, "rows": heatmap_rows}
    else:
        topic_heatmap = {"weeks": [], "rows": []}

    # --- 3. Domain-Vergleich wochenweise (letzte 8 Wochen) ---
    comp_df = df[df["date"] >= cutoff_8w].copy()
    comp_df["week"] = pd.to_datetime(comp_df["date"]).dt.strftime("%Y-W%W")
    domain_comparison = []
    all_weeks = sorted(comp_df["week"].unique()) if not comp_df.empty else []
    for domain in sorted(df["domain"].unique()):
        ddf = comp_df[comp_df["domain"] == domain]
        if ddf.empty:
            continue
        grouped = ddf.groupby("week")["orwell_index"].median().round(3)
        points = [float(grouped.get(w, None)) if w in grouped.index else None for w in all_weeks]
        if any(v is not None for v in points):
            domain_comparison.append({"domain": domain, "values": points})

    return {
        "trend_cards":       trend_cards,
        "topic_heatmap":     topic_heatmap,
        "domain_comparison": domain_comparison,
        "weeks":             all_weeks,
    }


def publisher_profiles(df: pd.DataFrame) -> list[dict]:
    """Publisher-Profil pro Domain: politische Strömungen + Abhängigkeits-Scores."""
    if df.empty:
        return []

    profiles: dict[str, dict] = {}

    for _, row in df.iterrows():
        domain = row.get("domain", "")
        if not domain:
            continue
        if domain not in profiles:
            profiles[domain] = {
                "domain":    domain,
                "artikel":   0,
                "stroemung": {},
                "abhaengigkeit": {k: {"positiv": 0, "negativ": 0, "neutral": 0} for k in _DEPENDENCY_ENTITIES},
            }
        p = profiles[domain]
        p["artikel"] += 1

        for label in row.get("politische_stroemung", []):
            p["stroemung"][label] = p["stroemung"].get(label, 0) + 1

        for t in row.get("manipulation_targets", []):
            if not isinstance(t, dict):
                continue
            entity = t.get("entity", "").lower()
            direction = t.get("direction", "neutral")
            if direction not in ("positiv", "negativ", "neutral"):
                direction = "neutral"
            for dim, keywords in _DEPENDENCY_ENTITIES.items():
                if any(kw in entity for kw in keywords):
                    p["abhaengigkeit"][dim][direction] += 1

    result = []
    for p in profiles.values():
        dep_scores = {}
        for dim, counts in p["abhaengigkeit"].items():
            total = counts["positiv"] + counts["negativ"] + counts["neutral"]
            if total == 0:
                score = None
            else:
                score = round((counts["positiv"] - counts["negativ"]) / total, 2)
            dep_scores[dim] = {
                "label":    _DEPENDENCY_LABELS[dim],
                "score":    score,
                "positiv":  counts["positiv"],
                "negativ":  counts["negativ"],
                "neutral":  counts["neutral"],
                "total":    total,
            }
        result.append({
            "domain":        p["domain"],
            "artikel":       p["artikel"],
            "stroemung":     dict(sorted(p["stroemung"].items(), key=lambda x: -x[1])),
            "abhaengigkeit": dep_scores,
        })

    return sorted(result, key=lambda x: -x["artikel"])


def daily_verlauf(df: pd.DataFrame, domain: str | None = None) -> list[dict]:
    """Tagesbasierter Median der numerischen Indikatoren, optional nach Domain gefiltert."""
    if domain:
        df = df[df["domain"] == domain]
    if df.empty:
        return []

    df = df.copy()
    df["date"] = pd.to_datetime(
        df["published_at"].where(df["published_at"].notna(), df.get("timestamp")),
        errors="coerce",
    ).dt.date
    df = df.dropna(subset=["date"])

    for col in ["orwell_index", "bernays_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    has_dk = "dunning_kruger_index" in df.columns
    if has_dk:
        df["dunning_kruger_index"] = pd.to_numeric(df["dunning_kruger_index"], errors="coerce")

    agg: dict = {
        "count":          ("orwell_index", "count"),
        "orwell_median":  ("orwell_index", "median"),
        "orwell_max":     ("orwell_index", "max"),
        "bernays_median": ("bernays_score", "median"),
        "bernays_max":    ("bernays_score", "max"),
    }
    if has_dk:
        agg["dk_median"] = ("dunning_kruger_index", "median")
        agg["dk_max"]    = ("dunning_kruger_index", "max")

    grouped = (
        df.groupby("date")
        .agg(**agg)
        .reset_index()
        .sort_values("date")
    )

    result = []
    for _, row in grouped.iterrows():
        entry: dict = {
            "date":           str(row["date"]),
            "count":          int(row["count"]),
            "orwell_median":  round(float(row["orwell_median"]), 3),
            "orwell_max":     round(float(row["orwell_max"]), 3),
            "bernays_median": round(float(row["bernays_median"]), 2),
            "bernays_max":    round(float(row["bernays_max"]), 2),
        }
        if has_dk and pd.notna(row.get("dk_median")):
            entry["dk_median"] = round(float(row["dk_median"]), 3)
            entry["dk_max"]    = round(float(row["dk_max"]), 3)
        result.append(entry)

    return result


def author_orwell(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Durchschnittlicher Orwell-Index pro Autor (mind. 2 Artikel)."""
    if "author" not in df.columns:
        return pd.DataFrame()
    filtered = df[df["author"].notna() & (df["author"] != "")]
    grouped = (
        filtered.groupby("author")["orwell_index"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "orwell_avg", "count": "artikel"})
    )
    return (
        grouped[grouped["artikel"] >= 2]
        .sort_values("orwell_avg")
        .head(n)
        .round(3)
    )


def print_report(n: int = 5) -> None:
    df = _load_dataframe()

    if df.empty:
        print("Keine Artikel in der Datenbank.")
        return

    total = len(df)
    print(f"\n{'='*55}")
    print(f"  NEWS ANALYSER — Statistik ({total} Artikel)")
    print(f"{'='*55}")

    print(f"\n[>>] Top {n} Manipulationstechniken:")
    for technique, count in top_techniques(df, n).items():
        bar = "#" * count
        print(f"  {technique:<30} {count:>3}x  {bar}")

    print(f"\n[O] Orwell-Index (Extremismus, 0.0 bis 1.0):")
    for label, value in orwell_distribution(df).items():
        print(f"  {label:<22} {value}")

    print(f"\n[B] Bernays Score (Manipulationsintensitaet, Techniken/1000 Woerter):")
    for label, value in bernays_distribution(df).items():
        print(f"  {label:<22} {value}")

    dk_dist = dunning_kruger_distribution(df)
    if dk_dist:
        print(f"\n[DK] Dunning-Kruger-Index (epistemische Ueberzeugheit, 0.0-1.0):")
        for label, value in dk_dist.items():
            print(f"  {label:<22} {value}")

    stroemungen = top_stroemungen(df)
    if not stroemungen.empty:
        print(f"\n[P] Politische Stroemungen (alle Artikel):")
        for label, count in stroemungen.items():
            bar = "#" * count
            print(f"  {label:<30} {count:>3}x  {bar}")

    print(f"\n[D] Top {n} Domains:")
    for domain, count in top_domains(df, n).items():
        print(f"  {domain:<35} {count:>3} Artikel")

    print(f"\n[S] Intendierte Emotionen:")
    for sentiment, count in sentiment_distribution(df).items():
        print(f"  {sentiment:<25} {count:>3}x")

    dom_df = domain_averages(df)
    if not dom_df.empty:
        has_dk = "dk_avg" in dom_df.columns
        header = f"  {'Portal':<35} {'Artikel':>7}  {'Orwell-Avg':>10}  {'Bernays-Avg':>11}"
        if has_dk:
            header += f"  {'DK-Avg':>6}"
        print(f"\n[~] Kennwert-Durchschnitt pro Nachrichtenportal:")
        print(header)
        print("  " + "-" * (len(header) - 2))
        for domain, row in dom_df.iterrows():
            line = (
                f"  {domain:<35} {int(row['artikel']):>7}"
                f"  {row['orwell_avg']:>10.3f}"
                f"  {row['bernays_avg']:>11.2f}"
            )
            if has_dk:
                line += f"  {row['dk_avg']:>6.3f}"
            print(line)

    entity_df = entity_targeting(df)
    if not entity_df.empty:
        print(f"\n[E] Manipulations-Targets (Entitaet x Richtung):")
        print(f"  {'Entitaet':<28} {'Richtung':<10} {'Anzahl':>6}  {'Bernays-Avg':>11}  Portale")
        print("  " + "-" * 80)
        for _, row in entity_df.iterrows():
            print(
                f"  {str(row['entity']):<28} {str(row['direction']):<10}"
                f" {int(row['anzahl']):>6}  {float(row['bernays_avg']):>11.2f}"
                f"  {row['domains']}"
            )

    thema_df = thema_bernays(df)
    if not thema_df.empty:
        print(f"\n[T] Bernays Score und Orwell-Index nach Themenbereich:")
        print(f"  {'Thema':<20} {'Artikel':>7}  {'Bernays-Avg':>11}  {'Orwell-Avg':>10}")
        print("  " + "-" * 54)
        for thema, row in thema_df.iterrows():
            print(
                f"  {thema:<20} {int(row['artikel']):>7}"
                f"  {row['bernays_avg']:>11.2f}"
                f"  {row['orwell_avg']:>10.3f}"
            )

    author_df = author_orwell(df, n)
    if not author_df.empty:
        print(f"\n[A] Autoren-Orwell-Index (mind. 2 Artikel, sortiert):")
        for author, row in author_df.iterrows():
            direction = "<" if row["orwell_avg"] < 0 else ">"
            print(f"  {author:<35} {row['orwell_avg']:+.3f} {direction}  ({int(row['artikel'])} Artikel)")

    print(f"\n{'='*55}\n")
