# Testergebnisse — Erster Proof of Concept

**Datum:** 22. Mai 2026  
**System:** news_analyser v0.1 — CLIConnector (claude-sonnet-4-6)  
**Metrik:** Orwell-Index (−1.0 bis +1.0)

---

## Methodische Vorbemerkungen

### Quellenauswahl und inhärenter Bias

Die Auswahl der Testquellen ist selbst ein Akt mit Bias-Potential und muss als solcher transparent gemacht werden.

Die Quellen wurden bewusst nach **ideologischer Breite** ausgewählt — von verifizierten historischen Propagandatexten über öffentlich-rechtliche Medien bis zu explizit positionierten modernen Quellen. Das Ziel war kein repräsentativer Querschnitt der deutschen Medienlandschaft, sondern ein **Kalibrierungstest** des Analyse-Systems über möglichst weite Teile der politischen Achse.

Folgende Verzerrungen sind in der Auswahl bewusst enthalten:

- **Thematische Konzentration**: Viele Artikel behandeln das Thema Lina E. — ein politisch hoch aufgeladenes Thema, das Quellen zu extremeren Aussagen verleitet als Routineberichterstattung. Die Ergebnisse sind daher nicht zwingend repräsentativ für das Gesamtprogramm einer Quelle.
- **Stichprobengröße**: Pro Quelle wurde maximal ein Artikel analysiert. Belastbare Aussagen über eine Redaktion erfordern deutlich mehr Datenpunkte.
- **Blinde Auswahl**: Der Tester hat die Artikel bewusst vor der Analyse nicht gelesen, um den eigenen Confirmation Bias zu reduzieren. Dennoch war die Quelle bekannt, was die Auswahl beeinflusst haben kann.
- **Historische Texte als Anker**: Die NS- und DDR-Texte dienen als Kalibrierungspunkte für bekannte Extreme, nicht als direkter Vergleich mit modernem Journalismus.

---

## Der Orwell-Index — Erklärung des Index

Der Orwell-Index ist eine vom LLM-Agenten vergebene Gleitkommazahl zwischen **−1.0** und **+1.0**. Er misst die **ideologische Ausrichtung** eines Textes, nicht seine journalistische Qualität.

### Skala

| Bereich | Bedeutung |
|---|---|
| `−1.0 bis −0.6` | Stark linksliberal / progressiv |
| `−0.6 bis −0.2` | Linksliberal |
| `−0.2 bis +0.2` | Weitgehend neutral |
| `+0.2 bis +0.6` | Rechtskonservativ |
| `+0.6 bis +1.0` | Stark rechtskonservativ / nationalistisch |

### Was der Score misst

Der Score bewertet *wohin* die rhetorischen Mittel eines Textes zeigen — welche Akteure, Positionen oder Narrative aufgewertet (+) bzw. abgewertet (−) werden. Er ist **kein Qualitätsurteil**: ein handwerklich sauberer Artikel kann einen hohen Score haben, ein schlecht recherchierter einen niedrigen.

### Was der Score nicht misst

- **Faktentreue**: Ein faktisch korrekter Artikel kann stark geframet sein.
- **Journalistische Sorgfalt**: Quellenwahl, Recherche und Ausgewogenheit fließen nicht direkt ein.
- **Absolute Neutralität**: Ein Score nahe 0.0 bedeutet nicht Abwesenheit von Perspektive, sondern dass sich die rhetorischen Mittel die Waage halten.

### Wie der Score entsteht

Der Agent bewertet den Text ganzheitlich anhand der erkannten Techniken, der Sprache, der Auswahl und Gewichtung von Fakten sowie der impliziten Narrative. Es handelt sich um eine **LLM-Schätzung**, keine mathematisch ableitbare Kennzahl — Reproduzierbarkeit ist hoch, aber nicht absolut. Wiederholte Analysen desselben Artikels können um ±0.1 schwanken.

### Kalibrierungspunkte aus diesem Test

| Referenz | Score | Bedeutung |
|---|---|---|
| NS Berufsbeamtengesetz 1933 | `+0.97` | Theoretisches Maximum — staatliche Staatspropaganda |
| DDR Aufbaugesetz 1950 | `−0.95` | Theoretisches Minimum — staatliche Staatspropaganda |
| Wikipedia (Lina E.) | `+0.20` | Praktische Neutralität bei redaktionell geprüftem Inhalt |

---

## Der Dunning-Kruger-Index — Erklärung des Index

Der Dunning-Kruger-Index ist eine vom LLM-Agenten vergebene Gleitkommazahl zwischen **0.0** und **1.0**. Er misst die **epistemische Überzeugheit** eines Textes — wie sicher Behauptungen aufgestellt werden, relativ zur evidenziellen Basis.

### Skala

| Bereich | Bedeutung |
|---|---|
| `0.0 bis 0.3` | Epistemisch bescheiden — Aussagen qualifiziert, Quellen belegt, Unsicherheit anerkannt |
| `0.3 bis 0.6` | Moderat überzeugt — gemischte Hedges und Gewissheitsaussagen |
| `0.6 bis 1.0` | Epistemisch überzeugt — definitive Behauptungen ohne Absicherung |

### Was der Index misst

Der Index bewertet das Verhältnis zwischen der **Sicherheit** mit der Aussagen getroffen werden und ihrer **evidenziellen Grundlage**. Hohe Werte entstehen durch: definitive Formulierungen ohne Quellenangaben, fehlende Hedges ("könnte", "laut", "möglicherweise"), Ignorieren von Gegenargumenten und Komplexitätsleugnung.

### Was der Index nicht misst

- **Faktentreue**: Ein faktisch korrekter Text kann hoch scoring, ein falscher niedrig.
- **Ideologische Richtung**: Der Index ist orthogonal zum Orwell-Index — jede politische Richtung kann bescheiden oder überheblich argumentieren.
- **Journalistische Qualität**: Sachberichte können niedrig scoring ohne besonders guten Journalismus zu sein.

### Kalibrierungspunkte aus diesem Test

| Referenz | DK-Index | Bedeutung |
|---|---|---|
| NS Berufsbeamtengesetz 1933 | `0.92` | Staatspropaganda mit absolutem Gewissheitsanspruch |
| danisch.de | `0.92` | Meinungsblog — Thesen ohne systematische Belege |
| Wikipedia (Lina E.) | `0.12` | Redaktionell geprüft, stark qualifiziert |
| MDR (Höcke/Wahl) | `0.12` | Reine Faktenberichterstattung (Wahlergebnisse) |

---

## Phase 1 — Quellen-Überblick: Verschiedene Quellen, ähnliches Thema

### Testdesign
Erster Funktionstest mit thematisch verwandten Artikeln über NATO und internationale Politik.

| Quelle | Artikel | Orwell-Index | Techniken (Anzahl) |
|---|---|---|---|
| t-online.de | NATO-Außenminister tagen in Schweden | `−0.55` | 6 |
| danisch.de | Mafia-Krise Angstpublica | `+0.93` | 9 |

### Beobachtungen
- Das System erkennt beide Pole korrekt und ohne erkennbare Eigenverzerrung.
- Danisch.de ist stilistisch kein klassisches Nachrichtenmedium sondern ein Meinungsblog — die hohe Technikdichte (9) spiegelt den kommentierenden, polemischen Stil wider.
- Beide Quellen nutzen dieselbe Grundausstattung: FUD, Loaded Language, Framing, Emotional Manipulation — nur mit umgekehrten Vorzeichen.

---

## Phase 2 — Öffentlich-Rechtliche Medien: ARD vs. MDR

### Testdesign
Vergleich von zentralen (Tagesschau/ARD) und regionalen (MDR) öffentlich-rechtlichen Medien, zunächst mit Außenpolitik-Themen.

| Quelle | Artikel | Orwell-Index | Techniken |
|---|---|---|---|
| Tagesschau (ARD) | USA Wahlrecht & Bürgerrechte | `−0.75` | 9 |
| MDR | Ukraine/NATO/Trump | `−0.25` | 5 |

### Beobachtungen
- Der MDR liegt deutlich näher an der Null als die Tagesschau — sowohl im Score als auch in der Technikdichte.
- Die Hypothese "regionale ÖR-Medien sind moderater" erhält erste Unterstützung.

---

## Phase 3 — MDR intern: Politische Themenabhängigkeit

### Testdesign
Vier MDR-Artikel zu politisch unterschiedlich aufgeladenen Themen, um zu prüfen ob der Score themenabhängig schwankt oder redaktionskulturell stabil ist.

| MDR-Artikel | Thema | Orwell-Index | Techniken |
|---|---|---|---|
| Ukraine/NATO | Außenpolitik (neutral) | `−0.25` | 5 |
| Mario Voigt/Plagiat | CDU-Politiker | `−0.30` | 6 |
| Kulturförderungsgesetz SA | AfD-relevantes Thema | `−0.45` | 6 |
| Björn Höcke/Landtagswahl | AfD-Wahlergebnis | `−0.20` | 3 |

### Beobachtungen
- Der MDR zeigt eine bemerkenswerte **Konsistenz** — alle Scores liegen zwischen −0.20 und −0.45.
- Der Höcke-Artikel ist der neutralste — vermutlich weil reine Wahlergebnisberichterstattung wenig Spielraum für Framing lässt (Zahlen sind Zahlen).
- Ein leichter Anstieg beim AfD-relevanten Kulturthema (−0.45) ist erkennbar, aber statistisch nicht belastbar.
- **Fazit**: MDR-Scores deuten auf Redaktionskultur hin, nicht auf themenabhängiges Framing.

---

## Phase 4 — Das Spektrum: Gleiches Thema, alle Quellen

### Testdesign
Das politisch maximal aufgeladene Thema "Lina E." wurde quer durch alle Quellentypen analysiert — von linksradikal bis rechtskonservativ — um die vollständige ideologische Achse abzubilden. Ergänzt durch Wikipedia als Neutralitäts-Kontrollgruppe.

| Quelle | Lager | Orwell-Index | Techniken |
|---|---|---|---|
| nd-aktuell | Linksradikal | `−0.82` | 8 |
| Tagesschau | ÖR / linksliberal | `+0.25`* | 5 |
| MDR Podcast | ÖR / regional | `−0.35` | 4 |
| MDR Meldung | ÖR / regional | `+0.30` | 2 |
| **Wikipedia** | **Neutral (Kontrollgruppe)** | **`+0.15`** | **3** |
| Junge Freiheit | Rechtskonservativ | `+0.85` | 7 |

*Tagesschau-Investigativ-Artikel über Lina E., nicht identisches Format

### Beobachtungen
- **Fast perfekte Symmetrie**: nd-aktuell bei −0.82, Junge Freiheit bei +0.85 — beide Extreme liefern ähnliche Technikdichten (7–8).
- **Wikipedia besteht den Neutralitätstest**: +0.15 bei 3 Techniken aus 69.000 Zeichen Text ist das stärkste Signal für Systemvalidität in diesem Test.
- **Tagesschau-Anomalie**: Der investigative Lina-E.-Artikel (+0.25) weicht deutlich vom Tagesschau-Außenpolitikartikel (−0.75) ab — ein Hinweis darauf dass Format und Autorenschaft innerhalb einer Redaktion stärker variieren als zwischen Redaktionen.
- **Kernbefund**: Alle Quellen nutzen denselben rhetorischen Werkzeugkasten. Der Orwell-Index misst die Richtung, nicht die Existenz von Framing.

---

## Phase 5 — Historische Kalibrierung

### Testdesign
Zwei historische Propagandatexte mit bekannter ideologischer Zuordnung als Anker für die Extrempunkte der Skala.

| Quelle | Epoche | Lager | Orwell-Index | Techniken |
|---|---|---|---|---|
| Gesetz zur Wiederherstellung des Berufsbeamtentums | NS 1933 | Rechtsextrem | `+1.00` | 7 |
| Aufbaugesetz DDR (Präambel) | SED 1950 | Linksextrem | `−0.92` | 7 |

### Beobachtungen
- Das NS-Gesetz erreicht den **theoretischen Maximalwert +1.00** — ein wichtiger Kalibrierungspunkt.
- Das DDR-Aufbaugesetz landet symmetrisch bei −0.92 und bestätigt die Skala an beiden Enden.
- **Technikdichte identisch** (7 bei beiden): Historische Staatspropaganda unterscheidet sich in der *Intensität* kaum von modernen Extremquellen (JF: 7, nd: 8) — nur die Beschönigung fehlt.
- Die **rhetorische Verwandtschaft** zwischen früher SED-Propaganda und NS-Rhetorik spiegelt sich im Ergebnis wider: beide nutzen Scapegoating, Loaded Language und Emotional Manipulation als Kernwerkzeuge.

---

## Gesamtübersicht

| Quelle | Orwell-Index | Bernays Score | DK-Index |
|---|---|---|---|
| NS Berufsbeamtengesetz 1933 | `+0.97` | 4.49 | **0.92** |
| danisch.de | `+0.88` | 8.93 | **0.92** |
| DDR Aufbaugesetz 1950 | `−0.95` | 6.22 | **0.88** |
| Junge Freiheit | `+0.75` | 15.54 | 0.72 |
| nd-aktuell | `−0.85` | 10.57 | 0.72 |
| Tagesschau (USA Wahlrecht) | `−0.65` | 6.00 | 0.62 |
| t-online.de | `−0.55` | 15.43 | 0.62 |
| MDR (Voigt/Plagiat) | `−0.30` | 5.01 | 0.55 |
| MDR (Kulturförderung) | `−0.45` | 6.08 | 0.30 |
| MDR (Lina E. Podcast) | `−0.45` | 8.47 | 0.25 |
| MDR (Lina E. Entlassung) | `+0.30` | 6.06 | 0.25 |
| MDR (Ukraine/NATO) | `−0.30` | 2.39 | 0.20 |
| Tagesschau (Lina E. investigativ) | `+0.28` | 5.51 | 0.22 |
| **Wikipedia** | **`+0.20`** | **0.40** | **0.12** |
| MDR (Höcke/Wahl) | `−0.25` | 3.29 | **0.12** |

---

## Schlussfolgerungen

### Was die Ergebnisse bedeuten

**1. Das System funktioniert und ist konsistent.**  
Wikipedia als bekannte Neutralitäts-Kontrollgruppe landet nahe der Null, historische Staatspropaganda an den Extremen. Das gibt dem Prompt-Design und dem Modell Glaubwürdigkeit.

**2. Framing ist universell — Richtung ist variabel.**  
Alle getesteten Quellen, von nd-aktuell bis Junge Freiheit, nutzen denselben rhetorischen Werkzeugkasten (Loaded Language, Framing, Emotional Manipulation). Der Orwell-Index misst nicht *ob* Framing stattfindet, sondern *wohin* es zeigt. Neutrale Berichterstattung ist die Ausnahme, nicht die Regel.

**3. Öffentlich-Rechtliche sind nicht neutral, aber moderater.**  
MDR und Tagesschau landen konsistent im negativen (linksliberalen) Bereich, aber deutlich entfernt von den ideologischen Extremen. Ihre Finanzierung durch Pflichtgebühren und ihr Neutralitätsanspruch spiegeln sich in moderateren Scores wider — aber nicht in Abwesenheit von Framing.

**4. Format und Autorenschaft variieren stärker als Redaktionskultur.**  
Der stärkste Tagesschau-Ausreißer kam nicht von einer anderen Quelle, sondern von einem anderen Format (Investigativ vs. Nachricht). Ein einzelner Artikel ist kein zuverlässiges Bild einer Redaktion.

**5. Die rhetorische DNA der modernen Medienlandschaft ist älter als das Internet.**  
Edward Bernays kodifizierte die Werkzeuge in den 1920ern. NS und SED haben sie perfektioniert. Die Scores der historischen Texte (+1.00 / −0.92) liegen nur marginal über den modernen Extremquellen (+0.93 / −0.82) — der Werkzeugkasten hat sich nicht verändert, nur der gesellschaftliche Kontext in dem er eingesetzt wird.

---

## Limitierungen und nächste Schritte

- **n=1 pro Quelle**: Für belastbare Aussagen werden mindestens 20–50 Artikel pro Quelle benötigt.
- **Themenverzerrung**: "Lina E." ist ein Ausnahmefall. Routineberichterstattung dürfte moderatere Scores produzieren.
- **Modell-Bias**: Der Analyse-Agent (Claude) hat selbst eine Trainingsdaten-basierte Weltsicht. Systemische Verzerrungen im Modell können die Scores beeinflussen.
- **Fehlende Gegenkontrolle**: Kein Test mit einer eindeutig rechtsextremen Quelle als Pendant zum nd-aktuell auf der linken Seite (Compact wäre die naheliegende Wahl).

Der nächste sinnvolle Schritt ist der Betrieb des RSS-Feed-Collectors über mehrere Wochen, um pro Quelle eine statistisch belastbare Stichprobengröße zu erreichen.
