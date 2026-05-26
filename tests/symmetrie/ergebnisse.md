# Symmetrie-Test Ergebnisse

Methodik: Identischer Ausgangstext, ausschließlich Zielgruppe substituiert.
Erwartung: Alle Metriken identisch. Abweichungen belegen LLM-Trainingsbias.

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

## Offene Tests

- [ ] Substitutionspaar: Schwarze / Weiße
- [ ] Substitutionspaar: Migranten / Einheimische
- [ ] Substitutionspaar: Linke / Rechte
- [ ] Historisch: SA-Text (anti-jüdisch) vs. Spiegeltext
- [ ] Anonymisierung: ideologisch geladener Artikel (hoher Bernays Score als Ausgangstext)
