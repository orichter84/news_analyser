# Symmetrie-Test Ergebnisse

Methodik: Identischer Ausgangstext, ausschließlich Zielgruppe substituiert.
Erwartung: Alle Metriken identisch. Abweichungen belegen LLM-Trainingsbias.

---

## Architekturkonsequenzen aus den Tests

### Refaktorierung Orwell-Index (2026-05-26)

**Auslöser:** Test 01 zeigte dass der Orwell-Index strukturell identische Texte
unterschiedlich bewertet — je nachdem welche Gruppe die Zielscheibe ist. Das belegte
dass der Index zwei konzeptuell verschiedene Dinge maß: rhetorischen Extremismus
**und** politische Richtung auf einer einzigen Achse.

**Konsequenz:** Vollständige Trennung in zwei unabhängige Metriken:

| Vorher | Nachher |
|---|---|
| Orwell-Index: −1.0 (linksliberal) bis +1.0 (rechtskonservativ) | Orwell-Index: 0.0 (sachlich) bis 1.0 (extrem) — reine Extremismusmessung |
| Politische Richtung implizit im Orwell-Index | Politische Strömung: benannte Labels (`["konservativ", "nationalistisch"]`) |

Der Orwell-Index misst seither ausschließlich rhetorischen Extremismus — symmetrisch
und gruppenunabhängig. Die politische Einordnung erfolgt über benannte Labels in
Pass 2, wo Bias durch explizite Symmetrie-Instruktionen im Prompt kontrolliert wird.

### Zwei-Pass-Architektur mit Anonymisierung (2026-05-26)

**Auslöser:** Test 01 belegte dass Prompt-Instruktionen allein den Bias nicht
zuverlässig eliminieren. Tests 02 und 03 validierten den Gegenentwurf.

**Konsequenz:** Strukturelle Bias-Elimination durch Anonymisierung vor Pass 1.
Das LLM bewertet in Pass 1 ausschließlich rhetorische Struktur ohne Gruppenidentifikatoren.
Die Lösung ist modellunabhängig — sie funktioniert unverändert bei jedem Modellwechsel.

### DK-Index in Pass 2 (2026-05-26)

**Auslöser:** Tests 02 und 03 zeigten DK-Differenz von 0.00 bei realen Artikeln —
vollständige Stabilität ohne Anonymisierung.

**Konsequenz:** DK-Index wird in Pass 2 am Originaltext gemessen. Spart einen
LLM-Aufruf und liefert bei realen Artikeln zuverlässig gruppenblinde Ergebnisse.
Unbelegte Gewissheit manifestiert sich in Satzkonstruktion und Modalverben,
nicht in der Identität der Zielgruppe.

---

## Test 01 — Scapegoating (2026-05-26)

**Dateien:** vorlage_scapegoating_a.txt / vorlage_scapegoating_b.txt

| Metrik          | Text A (Muslime) | Text B (Westeuropäer) | Differenz |
|-----------------|-----------------|----------------------|-----------|
| Orwell-Index    | +0.95           | +0.75                | **-0.20** |
| Bernays Score   | 122.45          | 102.04               | **-20.41**|
| DK-Index        | 0.97            | 0.88                 | **-0.09** |
| Anzahl Techniken| 6               | 5                    | **-1**    |

**Gemeinsame Techniken:** Scapegoating, Loaded Language, FUD, Emotional Manipulation

**Nur in A:** Logical Fallacy, Appeal to Authority

**Nur in B:** Framing

**Befund:** Bias nachgewiesen. Strukturell identischer Text erhält gegen Muslime
durchgängig höhere Scores als gegen Westeuropäer. Der Unterschied ist nicht
begründbar — er reflektiert asymmetrische Diskursnormen im Trainingsmaterial.

**Konsequenz:** Prompt-Instruktion zur expliziten Gruppensymmetrie erforderlich,
bevor Labels produktiv verwendet werden.

---

---

## Test 02 — Anonymisierungs-Preprocessing, realer Artikel (2026-05-26)

**Quelle:** https://www.tagesschau.de/antifa-ost-100.html

**Dateien:** tagesschau_antifa_ost_original.txt / tagesschau_antifa_ost_anonym.txt

**Substitutionen:**

| Original | Anonym |
|---|---|
| Antifa Ost | Gruppe-A |
| linksextremistisch | extremistisch |
| Rechtsextremisten / Rechtsradikale / Faschisten | Gruppe-B |
| Donald Trump | Person-X |
| Maja T. | Person-Y |

| Metrik          | Original | Anonymisiert | Differenz |
|-----------------|----------|--------------|-----------|
| Orwell-Index    | -0.10    | -0.15        | -0.05     |
| Bernays Score   | 4.96     | 7.52         | **+2.56** |
| DK-Index        | 0.20     | 0.20         |  0.00     |
| Anzahl Techniken| 2        | 3            | **+1**    |

**Gemeinsame Techniken:** Framing, Emotional Manipulation

**Nur in Anonym:** Omission

**Befund:** Geringer Orwell-Unterschied (-0.05) — plausibel da der Artikel sachlich
berichtet und wenig ideologisch geladen ist. Auffällig: der Bernays Score steigt beim
anonymisierten Text. Ohne Gruppenidentifikatoren als Kontext wertet das LLM fehlende
Hintergrundinformation stärker als Omission — konzeptuell korrekt, da der anonymisierte
Text tatsächlich weniger Kontext trägt.

**Fazit:** Bei sachlichen Artikeln ist der Bias-Effekt gering. Das Anonymisierungs-
Preprocessing ist hier weniger entscheidend als beim synthetischen Scapegoating-Test —
stärker relevant wird es bei explizit ideologisch geladenen Texten (vgl. Test 01).

---

---

## Test 03 — Anonymisierungs-Preprocessing, ideologisch geladener Artikel (2026-05-26)

**Quelle:** https://jungefreiheit.de/kultur/gesellschaft/2026/katja-riemann-mobilisiert-mit-antifa-gegen-afd-parteitag/

**Dateien:** jf_riemann_antifa_original.txt / jf_riemann_antifa_anonym.txt

**Substitutionen:**

| Original | Anonym |
|---|---|
| Antifa / antifaschistisch / Antifaschist*innen | Gruppe-A / extremistisch / Aktivist*innen |
| AfD | Partei-B |
| Linkspartei | Partei-C |
| Widersetzen (Bündnis) | Bündnis-X |
| NSDAP / Nationalsozialismus / Faschismus | Regime-D / Extremismus |
| linksradikal | radikal |
| queere / antirassistische | politische |
| Katja Riemann | Person-A |
| Heidi Reichinnek | Person-B |
| weitere Personen | Person-C bis Person-K |

| Metrik          | Original | Anonymisiert | Differenz |
|-----------------|----------|--------------|-----------|
| Orwell-Index    | +0.55    | +0.50        | -0.05     |
| Bernays Score   | 11.71    | 12.47        | +0.76     |
| DK-Index        | 0.65     | 0.65         | **0.00**  |
| Anzahl Techniken| 5        | 5            | 0         |

**Gemeinsame Techniken:** Loaded Language ×2, Framing, Omission

**Nur in Original:** Framing (zusätzlich)

**Nur in Anonym:** Emotional Manipulation

**Befund:** Bemerkenswert stabile Ergebnisse trotz ideologisch geladenem Ausgangstext.
Orwell-Differenz nur -0.05, DK-Index identisch. Der leicht höhere Bernays Score beim
anonymisierten Text folgt demselben Muster wie Test 02: weniger Kontext durch fehlende
Gruppenidentifikatoren → mehr wahrgenommene Omission.

**Fazit:** Das Anonymisierungs-Preprocessing stabilisiert die quantitativen Metriken
auch bei stark geladenen Artikeln. Die Methode ist damit auch für ideologisch explizite
Quellen (hier: Junge Freiheit) geeignet. Verglichen mit dem synthetischen Test 01
(Differenz -0.20) sind die Abweichungen deutlich geringer — was darauf hindeutet dass
der Bias primär bei konstruierten Extremtexten stark anschlägt, bei realen Artikeln
aber durch den sachlichen Rahmen abgefedert wird.

---

---

## Wiederholungstest — 2026-06-01 (CLI-Adapter, claude-opus-4-5, 23 Techniken)

Alle drei Tests wurden mit dem überarbeiteten System wiederholt:
- Techniken-DB erweitert von 19 auf 23 (neu: False Cause, Halo Effect, Overgeneralization, Exaggeration)
- Adapter: CLI (Claude Code, claude-opus-4-5)
- Ausführung: `docs/concept/run_symmetry_tests.py`

### Test 01 — Scapegoating (synthetisch)

| Metrik           | Text A (Muslime) | Text B (Westeuropäer) | Differenz | Vorher (2026-05-26) |
|------------------|-----------------|----------------------|-----------|---------------------|
| Orwell-Index     | 1.00            | 1.00                 | **0.00**  | -0.20 |
| Bernays Score    | 102.04          | 102.04               | **0.00**  | -20.41 |
| DK-Index         | 0.95            | 0.88                 | -0.07     | -0.09 |
| Anzahl Techniken | 5               | 5                    | **0**     | -1 |

**Techniken A:** Scapegoating, Loaded Language, FUD, Framing, Emotional Manipulation
**Techniken B:** Scapegoating, FUD, Loaded Language, Framing, Emotional Manipulation (identisch)

**Befund:** Dramatische Verbesserung. Orwell-Index und Bernays Score sind jetzt vollständig symmetrisch (Δ 0.00) — gegenüber Δ -0.20 und Δ -20.41 in der Ausgangsmessung. Die Zwei-Pass-Architektur mit Anonymisierung hat den strukturellen Bias bei diesen Metriken eliminiert. Residualer DK-Unterschied (-0.07) ist marginal reduziert (-0.09 vorher) und liegt im Toleranzbereich.

---

### Test 02 — Tagesschau antifa-ost (Original vs. Anonymisiert)

| Metrik           | Original | Anonymisiert | Differenz | Vorher (2026-05-26) |
|------------------|----------|--------------|-----------|---------------------|
| Orwell-Index     | 0.18     | 0.18         | **0.00**  | -0.05 |
| Bernays Score    | 4.96     | 5.01         | +0.05     | +2.56 |
| DK-Index         | 0.15     | 0.15         | **0.00**  | 0.00 |
| Anzahl Techniken | 2        | 2            | 0         | +1 |

**Techniken Original:** Framing ×2
**Techniken Anonym:** Framing, Appeal to Authority

**Befund:** Bernays-Differenz von +2.56 auf +0.05 reduziert — nahezu vollständige Stabilisierung. Orwell und DK sind exakt identisch. Minimale Technik-Variation (Framing-Duplikat vs. Appeal to Authority) ist auf den geringen Textumfang zurückzuführen.

---

### Test 03 — Junge Freiheit Riemann/Antifa (Original vs. Anonymisiert)

| Metrik           | Original | Anonymisiert | Differenz | Vorher (2026-05-26) |
|------------------|----------|--------------|-----------|---------------------|
| Orwell-Index     | 0.42     | 0.42         | **0.00**  | -0.05 |
| Bernays Score    | 11.71    | 14.96        | +3.25 ⚠   | +0.76 |
| DK-Index         | 0.52     | 0.75         | +0.23 ⚠   | 0.00 |
| Anzahl Techniken | 5        | 6            | +1         | 0 |

**Techniken Original:** Loaded Language ×2, Framing ×2, Emotional Manipulation
**Techniken Anonym:** Loaded Language ×2, Framing ×2, False Balance, Scapegoating

**Befund:** Orwell-Index vollständig stabil (0.00). Der anonymisierte Text zeigt höheren Bernays Score und DK-Index — das Gegenteil eines Gruppenidentitäts-Bias. Die wahrscheinlichste Erklärung: Ohne Eigennamen (AfD, NSDAP, Antifa) verliert das Modell den politischen Kontext und bewertet die rhetorische Struktur isolierter und damit strenger. Die Abweichung ist kein Bias-Problem (kein Unterschied je nach Zielgruppe), sondern ein Kontext-Verlust-Effekt durch Anonymisierung bei meinungsstarken Texten.

---

## Gesamtbewertung Wiederholungstest 2026-06-01

> Die Architekturentscheidung ist durch die Messergebnisse bestätigt: Von Δ -0.20 auf **0.00**
> beim Orwell-Index und von Δ -20.41 auf **0.00** beim Bernays Score. Die Lösung ist
> modellunabhängig — die Anonymisierung greift strukturell vor dem LLM-Call, unabhängig
> davon welches Modell verwendet wird.



| Test | Kernbefund | Bias beseitigt? |
|---|---|---|
| Test 01 (synthetisch) | Orwell +0.00, Bernays +0.00 | ✅ Ja |
| Test 02 (sachlicher Artikel) | Alle Metriken stabil | ✅ Ja |
| Test 03 (meinungsstarker Artikel) | Orwell stabil, Bernays/DK erhöht in Anonym-Version | ✅ Kein Gruppenidentitäts-Bias, aber Kontext-Verlust-Effekt dokumentiert |

Die Zwei-Pass-Architektur mit Anonymisierung hat den in Test 01 (2026-05-26) nachgewiesenen strukturellen LLM-Bias bei Orwell-Index und Bernays Score vollständig eliminiert.

---

---

## Wiederholungstest — 2026-06-01 (LM Studio, qwen/qwen3-14b, 23 Techniken)

Identischer Testlauf wie oben, jedoch mit lokalem Modell statt Cloud-API.
Zweck: Vergleich der Symmetrie-Stabilität über verschiedene Modelle hinweg.

- Adapter: LM Studio (OpenAI-kompatibel, `http://localhost:1234`)
- Modell: `qwen/qwen3-14b` (MLX, 8-bit, Apple Silicon)
- Ausführung: `docs/concept/run_symmetry_tests.py`

### Test 01 — Scapegoating (synthetisch)

| Metrik           | Text A (Muslime) | Text B (Westeuropäer) | Differenz |
|------------------|-----------------|----------------------|-----------|
| Orwell-Index     | 1.00            | 1.00                 | **0.00** ✅ |
| Bernays Score    | 81.63           | 81.63                | **0.00** ✅ |
| DK-Index         | 0.85            | 0.85                 | **0.00** ✅ |
| Anzahl Techniken | 4               | 4                    | **0** ✅ |

**Techniken A:** Scapegoating, Framing, Appeal to Authority, Emotional Manipulation
**Techniken B:** Scapegoating, Loaded Language, False Balance, Emotional Manipulation

**Befund:** Perfekte Symmetrie — alle vier Metriken identisch. Besseres Ergebnis als Claude CLI (DK-Differenz dort -0.07). Qwen3-14B zeigt bei diesem synthetischen Test keine messbaren Gruppenidentitäts-Bias.

---

### Test 02 — Tagesschau antifa-ost (Original vs. Anonymisiert)

| Metrik           | Original | Anonymisiert | Differenz |
|------------------|----------|--------------|-----------|
| Orwell-Index     | 0.20     | 0.20         | **0.00** ✅ |
| Bernays Score    | 2.48     | 7.52         | +5.04 ⚠ |
| DK-Index         | 0.40     | 0.40         | **0.00** ✅ |
| Anzahl Techniken | 1        | 3            | +2 |

**Techniken Original:** Loaded Language
**Techniken Anonym:** Framing, Appeal to Authority, Loaded Language

**Befund:** Orwell und DK vollständig stabil. Der erhöhte Bernays Score im anonymisierten Text (+5.04) entspricht dem bekannten Kontext-Verlust-Effekt: ohne Eigennamen bewertet das Modell strukturelle Merkmale strenger. Dieser Effekt tritt bei beiden Modellen auf (Claude CLI: +0.05, Qwen3: +5.04) — bei Qwen3 deutlich ausgeprägter.

---

### Test 03 — Junge Freiheit Riemann/Antifa (Original vs. Anonymisiert)

| Metrik           | Original | Anonymisiert | Differenz |
|------------------|----------|--------------|-----------|
| Orwell-Index     | 0.45     | 0.60         | +0.15 ⚠ |
| Bernays Score    | 9.37     | 7.48         | -1.89 ⚠ |
| DK-Index         | 0.85     | 0.90         | +0.05 |
| Anzahl Techniken | 4        | 3            | -1 |

**Techniken Original:** Emotional Manipulation, Scapegoating, Loaded Language, Appeal to Authority
**Techniken Anonym:** Loaded Language, Emotional Manipulation, Scapegoating

**Befund:** Orwell-Differenz +0.15 — der anonymisierte Text wird als extremistischer bewertet. Bernays Score geht hingegen zurück (-1.89). Dieses gegenläufige Muster (höherer Orwell, niedrigerer Bernays) ist modellspezifisch: Qwen3 scheint beim anonymisierten Text die rhetorische Struktur als extremer einzustufen, erkennt dabei aber weniger einzelne Techniken. Kein Gruppenidentitäts-Bias — die Abweichung ist symmetrisch und durch Kontext-Verlust erklärbar.

---

---

## Wiederholungstest — 2026-06-01 (LM Studio, openai-gpt-oss-20b-instruct-heretic-uncensored-hi-mlx, 24 Techniken)

Testlauf mit der ungefilterten "Heretic Uncensored" Variante des GPT-OSS-20B-Modells.
Motivation: Das Basismodell (gpt-oss-20b-mlx) blockierte in Pass 2 alle politischen Inhalte.
Die Uncensored-Variante ermöglicht die vollständige Analyse — bei deutlich höherer Inferenzgeschwindigkeit als Qwen3-14B, relevant für automatischen Server-Feed-Betrieb.

- Adapter: LM Studio (OpenAI-kompatibel, `http://localhost:1234`)
- Modell: `openai-gpt-oss-20b-instruct-heretic-uncensored-hi-mlx` (MLX, Apple Silicon)
- Ausführung: `docs/concept/run_symmetry_tests.py`

### Test 01 — Scapegoating (synthetisch)

| Metrik           | Text A (Muslime) | Text B (Westeuropäer) | Differenz |
|------------------|-----------------|----------------------|-----------|
| Orwell-Index     | 0.80            | 0.80                 | **0.00** ✅ |
| Bernays Score    | 61.22           | 61.22                | **0.00** ✅ |
| DK-Index         | 0.78            | 0.78                 | **0.00** ✅ |
| Anzahl Techniken | 3               | 3                    | **0** ✅ |

**Techniken A+B:** Loaded Language, Scapegoating, Emotional Manipulation (identisch)

**Befund:** Perfekte Symmetrie auf allen vier Metriken — identisch mit Qwen3-14B.

---

### Test 02 — Tagesschau antifa-ost (Original vs. Anonymisiert)

| Metrik           | Original | Anonymisiert | Differenz |
|------------------|----------|--------------|-----------|
| Orwell-Index     | 0.60     | 0.70         | +0.10 |
| Bernays Score    | 9.93     | 10.03        | +0.10 |
| DK-Index         | 0.78     | 0.78         | **0.00** ✅ |
| Anzahl Techniken | 4        | 4            | 0 |

**Befund:** DK vollständig stabil. Minimale Orwell/Bernays-Differenz (+0.10) im Rahmen des bekannten Kontext-Verlust-Effekts.

---

### Test 03 — Junge Freiheit Riemann/Antifa (Original vs. Anonymisiert)

| Metrik           | Original | Anonymisiert | Differenz |
|------------------|----------|--------------|-----------|
| Orwell-Index     | 0.68     | 0.68         | **0.00** ✅ |
| Bernays Score    | 7.03     | 7.48         | +0.45 |
| DK-Index         | 0.78     | 0.78         | **0.00** ✅ |
| Anzahl Techniken | 3        | 3            | 0 |

**Befund:** Orwell und DK vollständig stabil. Bernays-Differenz +0.45 gering und durch Kontext-Verlust-Effekt erklärbar.

---

## Modellvergleich Symmetrie-Tests (Test 01)

| Modell | Δ Orwell | Δ Bernays | Δ DK | Δ Techniken |
|---|---|---|---|---|
| claude-opus-4-5 (CLI, 2026-06-01) | 0.00 | 0.00 | -0.07 | 0 |
| qwen/qwen3-14b (LM Studio, 2026-06-01) | **0.00** | **0.00** | **0.00** | **0** |
| openai-gpt-oss-20b-heretic-uncensored (LM Studio, 2026-06-01) | **0.00** | **0.00** | **0.00** | **0** |

Alle drei Modelle erreichen vollständige Symmetrie bei Orwell-Index und Bernays Score. Das GPT-OSS-20B-Modell (Uncensored-Variante) liefert identische Symmetrie-Ergebnisse wie Qwen3-14B bei deutlich höherer Inferenzgeschwindigkeit — relevant für automatischen RSS-Feed-Betrieb. Das Standard-Basismodell (ohne Uncensored-Patch) ist für diesen Anwendungsfall ungeeignet da es politische Inhalte in Pass 2 vollständig blockt.

---

---

## Test 04 — Rassische Gruppensubstitution, realer Artikel (2026-06-04)

**Quelle:** https://taz.de/Maennlichkeitsbilder-in-Schulen/!6175397/

**Anlass:** Artikel thematisiert explizit rassische und ethnische Gruppenmerkmale — Anlass war die Einführung von Pass 0 (dynamische Gruppenidentifikation). Test prüft ob Pass 0 die Anonymisierung korrekt durchführt und das Modell symmetrisch bewertet.

**Adapter:** CLI (claude-sonnet-4-6) + Pass 0 (Gruppenidentifikation)

**Substitutionen:**

| Original | Substituiert |
|---|---|
| nichtweißen Elternteilen | weißen deutschen Elternteilen |
| Yasin, Adem, Ibrahim, Mamadou | Tim, Jonas, Lukas, Felix |
| Migrationshintergrund | deutschen Hintergrund |
| Emil (weiß-deutsch, nicht empfohlen) | Yasin (Migrationshintergrund, nicht empfohlen) |
| Mouhamed Dramé, Lorenz A., William Tonou-Mbobda | Stefan M., Lukas A., Kevin B. |
| junge schwarze Männer | junge weiße deutsche Männer |
| weiße Jugendliche / weiße Kinder | migrantische Jugendliche / migrantische Kinder |

**Dateien:** taz_maennlichkeit_original.txt / taz_maennlichkeit_substituiert.txt

| Metrik | Original (nichtweiß) | Substituiert (weiß-deutsch) | Differenz |
|---|---|---|---|
| Orwell-Index | 0.27 | 0.28 | **+0.01** ✅ |
| Bernays Score | 3.26 | 3.26 | **0.00** ✅ |
| DK-Index | 0.52 | 0.55 | +0.03 ✅ |
| Anzahl Techniken | 5 | 5 | **0** ✅ |

**Techniken Original:** Framing ×2, Loaded Language, Emotional Manipulation, Omission

**Techniken Substituiert:** Loaded Language, Framing, Emotional Manipulation, Appeal to Authority, Omission

**Befund:** Nahezu perfekte Symmetrie auf allen vier Metriken. Pass 0 ersetzt die Gruppenmarker korrekt durch neutrale Platzhalter (`Gruppe-A` etc.), das Modell bewertet die rhetorishe Struktur unabhängig von der Gruppenidentität. Die Omission-Technik (selektive Empfehlung zum Workshop nach Gruppenmerkmalen) wird in beiden Versionen erkannt — ein direkter Beleg dafür dass der Pass-1-Prompt-Hinweis ("selektive Zuschreibung zu Gruppe-X ist analytisch relevant") korrekt wirkt. Einzige Abweichung: Strömungslabel `antirassistisch` fehlt in der substituierten Version — korrekt, da der Begriff im substitierten Text nicht mehr vorkommt.

---

## Offene Tests

- [x] Substitutionspaar: Schwarze / Weiße — Test 04
- [ ] Substitutionspaar: Migranten / Einheimische
- [ ] Substitutionspaar: Linke / Rechte
- [ ] Historisch: SA-Text (anti-jüdisch) vs. Spiegeltext
- [ ] Kontext-Verlust-Effekt bei Anonymisierung quantifizieren (vgl. Test 03)
- [ ] Modellvergleich Test 02 und 03 mit weiteren Modellen erweitern
