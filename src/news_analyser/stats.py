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


def top_domains(df: pd.DataFrame, n: int = 5) -> pd.Series:
    """Domains mit den meisten analysierten Artikeln."""
    return df["domain"].value_counts().head(n)


def sentiment_distribution(df: pd.DataFrame) -> pd.Series:
    """Verteilung der intendierten Emotionen."""
    return df["intended_sentiment"].value_counts()


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

    print(f"\n📊 Top {n} Manipulationstechniken:")
    for technique, count in top_techniques(df, n).items():
        bar = "█" * count
        print(f"  {technique:<30} {count:>3}x  {bar}")

    print(f"\n🔵 Orwell-Index (ideologische Richtung, −1.0 bis +1.0):")
    for label, value in orwell_distribution(df).items():
        print(f"  {label:<22} {value}")

    print(f"\n🔴 Bernays Score (Manipulationsintensität, Techniken/1000 Wörter):")
    for label, value in bernays_distribution(df).items():
        print(f"  {label:<22} {value}")

    print(f"\n🌐 Top {n} Domains:")
    for domain, count in top_domains(df, n).items():
        print(f"  {domain:<35} {count:>3} Artikel")

    print(f"\n😤 Intendierte Emotionen:")
    for sentiment, count in sentiment_distribution(df).items():
        print(f"  {sentiment:<25} {count:>3}x")

    author_df = author_orwell(df, n)
    if not author_df.empty:
        print(f"\n✍️  Autoren-Orwell-Index (mind. 2 Artikel, sortiert):")
        for author, row in author_df.iterrows():
            direction = "←" if row["orwell_avg"] < 0 else "→"
            print(f"  {author:<35} {row['orwell_avg']:+.3f} {direction}  ({int(row['artikel'])} Artikel)")

    print(f"\n{'='*55}\n")
