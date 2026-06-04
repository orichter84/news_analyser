"""
Symmetrie-Test Runner — führt alle Bias-Validierungstests durch.

Verwendung:
    python docs/konzept/run_symmetry_tests.py

Gibt Ergebnisse tabellarisch aus und aktualisiert bias-validation.md.
"""
import sys
import json
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from news_analyser.scraper import Article
from news_analyser.agents.analyzer import analyze_article

BASE = Path(__file__).parent / "bias-test-cases"


def make_article(path: Path, url: str) -> Article:
    text = path.read_text(encoding="utf-8").strip()
    words = text.split()
    return Article(
        url=url,
        domain="bias-test",
        title=path.stem,
        author="",
        published_at="2026-05-26T00:00:00Z",
        fetched_at="2026-05-26T00:00:00Z",
        text=text,
        word_count=len(words),
        is_paywall=False,
    )


def run(label: str, article: Article) -> dict:
    print(f"  Analysiere: {label} ...", flush=True)
    result = analyze_article(article)
    if result is None:
        print(f"  [!] Fehler bei {label}")
        return {}
    ft = result.get("framing_target", {})
    techniques = result.get("detected_techniques", [])
    return {
        "label":           label,
        "orwell_index":    round(float(ft.get("orwell_index", 0.0)), 2),
        "bernays_score":   round(len(techniques) / max(article.word_count, 1) * 1000, 2),
        "dk_index":        round(float(ft.get("dunning_kruger_index", 0.0)), 2),
        "technique_count": len(techniques),
        "techniques":      [t["technique"] for t in techniques],
        "llm_model":       result.get("llm_model", "?"),
    }


def compare(a: dict, b: dict) -> dict:
    if not a or not b:
        return {"error": "Ein oder beide Läufe fehlgeschlagen — kein Vergleich möglich"}
    return {
        "orwell_diff":   round(b["orwell_index"]  - a["orwell_index"],  2),
        "bernays_diff":  round(b["bernays_score"] - a["bernays_score"], 2),
        "dk_diff":       round(b["dk_index"]      - a["dk_index"],      2),
        "tech_diff":     b["technique_count"]     - a["technique_count"],
    }


def print_result(r: dict):
    print(f"    Orwell-Index:    {r['orwell_index']}")
    print(f"    Bernays Score:   {r['bernays_score']}")
    print(f"    DK-Index:        {r['dk_index']}")
    print(f"    Techniken ({r['technique_count']}):   {', '.join(r['techniques'])}")
    print(f"    Modell:          {r['llm_model']}")


def print_diff(d: dict):
    if "error" in d:
        print(f"    ⚠ {d['error']}")
        return
    def flag(v): return " ⚠" if abs(v) > 0.1 else ""
    print(f"    Δ Orwell:   {d['orwell_diff']:+.2f}{flag(d['orwell_diff'])}")
    print(f"    Δ Bernays:  {d['bernays_diff']:+.2f}{flag(d['bernays_diff'])}")
    print(f"    Δ DK:       {d['dk_diff']:+.2f}{flag(d['dk_diff'])}")
    print(f"    Δ Techniken:{d['tech_diff']:+d}")


# ── Test 01: Scapegoating (synthetisch) ──────────────────────────────────────
print("\n=== Test 01 — Scapegoating (synthetisch) ===")
r01a = run("Text A (Muslime)",       make_article(BASE / "vorlage_scapegoating_a.txt", "bias-test://scapegoating-a"))
r01b = run("Text B (Westeuropäer)", make_article(BASE / "vorlage_scapegoating_b.txt", "bias-test://scapegoating-b"))
d01  = compare(r01a, r01b)
print(f"\n  Text A (Muslime):")
print_result(r01a)
print(f"\n  Text B (Westeuropäer):")
print_result(r01b)
print(f"\n  Differenz (B - A):")
print_diff(d01)

# ── Test 02: Tagesschau (Original vs. Anonym) ────────────────────────────────
print("\n=== Test 02 — Tagesschau antifa-ost (Original vs. Anonymisiert) ===")
r02a = run("Original",       make_article(BASE / "tagesschau_antifa_ost_original.txt", "bias-test://tagesschau-original"))
r02b = run("Anonymisiert",   make_article(BASE / "tagesschau_antifa_ost_anonym.txt",   "bias-test://tagesschau-anonym"))
d02  = compare(r02a, r02b)
print(f"\n  Original:")
print_result(r02a)
print(f"\n  Anonymisiert:")
print_result(r02b)
print(f"\n  Differenz (Anonym - Original):")
print_diff(d02)

# ── Test 03: Junge Freiheit (Original vs. Anonym) ────────────────────────────
print("\n=== Test 03 — Junge Freiheit Riemann/Antifa (Original vs. Anonymisiert) ===")
r03a = run("Original",     make_article(BASE / "jf_riemann_antifa_original.txt", "bias-test://jf-original"))
r03b = run("Anonymisiert", make_article(BASE / "jf_riemann_antifa_anonym.txt",   "bias-test://jf-anonym"))
d03  = compare(r03a, r03b)
print(f"\n  Original:")
print_result(r03a)
print(f"\n  Anonymisiert:")
print_result(r03b)
print(f"\n  Differenz (Anonym - Original):")
print_diff(d03)

# ── JSON-Rohdaten speichern ───────────────────────────────────────────────────
results = {
    "run_date": datetime.date.today().isoformat(),
    "test01": {"a": r01a, "b": r01b, "diff": d01},
    "test02": {"original": r02a, "anonym": r02b, "diff": d02},
    "test03": {"original": r03a, "anonym": r03b, "diff": d03},
}
out = BASE / "symmetry_test_results_latest.json"
out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"\n✓ Rohdaten gespeichert: {out}")
print("\nDone.")
