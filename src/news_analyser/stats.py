"""
Statistik-Auswertung der gespeicherten Artikel-Analysen.

Verwendung:
    python run.py --stats
    python run.py --stats --top 10
"""

import json
from collections import Counter
from typing import Any

import pandas as pd

from .db_storage import _get_collection


def _load_dataframe() -> pd.DataFrame:
    """Lädt alle gespeicherten Metadaten aus ChromaDB als DataFrame."""
    collection = _get_collection()
    result = collection.get(include=["metadatas"])

    if not result["metadatas"]:
        return pd.DataFrame()

    df = pd.DataFrame(result["metadatas"])
    df["technique_names"] = df["technique_names"].apply(json.loads)
    return df


def top_techniques(df: pd.DataFrame, n: int = 5) -> pd.Series:
    """Häufigste Manipulationstechniken über alle Artikel."""
    all_techniques = [t for row in df["technique_names"] for t in row]
    return pd.Series(Counter(all_techniques)).sort_values(ascending=False).head(n)


def bias_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """Statistische Kennzahlen der Bias-Scores."""
    scores = df["bias_score"].astype(float)
    return {
        "mean":   round(scores.mean(), 3),
        "median": round(scores.median(), 3),
        "std":    round(scores.std(), 3),
        "min":    round(scores.min(), 3),
        "max":    round(scores.max(), 3),
        "links (<-0.2)":   int((scores < -0.2).sum()),
        "neutral (-0.2–0.2)": int(((scores >= -0.2) & (scores <= 0.2)).sum()),
        "rechts (>0.2)":   int((scores > 0.2).sum()),
    }


def top_domains(df: pd.DataFrame, n: int = 5) -> pd.Series:
    """Domains mit den meisten analysierten Artikeln."""
    return df["domain"].value_counts().head(n)


def sentiment_distribution(df: pd.DataFrame) -> pd.Series:
    """Verteilung der intendierten Emotionen."""
    return df["intended_sentiment"].value_counts()


def print_report(n: int = 5) -> None:
    df = _load_dataframe()

    if df.empty:
        print("Keine Artikel in der Datenbank.")
        return

    total = len(df)
    print(f"\n{'='*50}")
    print(f"  NEWS ANALYSER — Statistik ({total} Artikel)")
    print(f"{'='*50}")

    print(f"\n📊 Top {n} Manipulationstechniken:")
    for technique, count in top_techniques(df, n).items():
        bar = "█" * count
        print(f"  {technique:<30} {count:>3}x  {bar}")

    print(f"\n⚖️  Bias-Score-Verteilung:")
    for label, value in bias_distribution(df).items():
        print(f"  {label:<22} {value}")

    print(f"\n🌐 Top {n} Domains:")
    for domain, count in top_domains(df, n).items():
        print(f"  {domain:<35} {count:>3} Artikel")

    print(f"\n😤 Intendierte Emotionen:")
    for sentiment, count in sentiment_distribution(df).items():
        print(f"  {sentiment:<25} {count:>3}x")

    print(f"\n{'='*50}\n")
