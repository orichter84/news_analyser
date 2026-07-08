# Konzeptentwurf: Gestaffelte Hybrid-Erkennung von Manipulationstechniken

## Ausgangslage

Alternative zum Fine-Tuning eines Foundation Models: RAG-gestützte Erkennung auf Basis
bereits verifizierter, in Chroma abgelegter Beispiele (Technik + Zitat). Statt eines
einzelnen Erkennungslaufs wird die Erkennung nach sprachlicher Ebene in drei parallele,
unabhängige Läufe aufgeteilt.

## Grundproblem der bisherigen Ansätze

- **Fine-Tuning**: Trainingsmenge muss pro Technik-Klasse ausreichend groß sein (Richtwert
  200–500 Beispiele minimum), Sammlung kostet Zeit, Retraining bei jedem neuen Beispiel nötig.
- **Reines RAG mit Nearest-Neighbor**: Standard-Embeddings optimieren auf semantische statt
  strukturelle/rhetorische Ähnlichkeit. Risiko: thematisch nahe, aber technisch irrelevante
  Treffer (False Positives) bzw. thematisch entfernte, aber technisch identische Fälle werden
  verpasst (False Negatives).
- **Mehrfachzählungs-Problem** (bekannt aus Feature-Branch-Regression): Mehrfache Vorkommen
  derselben Technik im Artikel müssen als separate Instanzen gezählt werden, nicht binär
  zusammengefasst.

## Architektur: Drei parallele Läufe nach Technik-Klasse

Jede Technik wird eindeutig einer Erkennungsklasse zugeordnet, abhängig davon, auf welcher
Textebene sie sich zeigt. Eine Technik **kann in mehreren Klassen gleichzeitig** vorkommen,
je nach konkreter Ausprägung im Text.

### Klasse 1 – Satzebene (NN only, kein LLM)

- Granularität: einzelner Satz
- Methode: Embedding des Satzes, Nearest-Neighbor-Suche gegen Chroma-Referenzbeispiele,
  Label wird bei ausreichender Nähe übernommen
- Geeignet für: Techniken mit festem sprachlichem Muster, die sich lokal in einem Satz
  äußern (z. B. starke emotionale Aufladung, Ad-hominem-Formulierungen)
- Kostenprofil: rein lokal, kein API-Call, günstig und schnell
- **Offener Punkt**: Distanz-Schwellenwert muss kalibriert werden (Symmetrietest-Ansatz wie
  bei den bestehenden Indikatoren), da die Distanz allein keine inhaltliche Prüfung ersetzt

### Klasse 2 – Overlap-Fenster (NN + LLM Hybrid)

- Granularität: überlappende Satzfenster (z. B. 2–3 Sätze, gleitend), **keine
  Einzelsatzbetrachtung**
- Methode: Fenster embedden, k ähnlichste Referenzbeispiele aus Chroma abrufen, diese als
  Few-Shot-Kontext in den LLM-Prompt einbetten, LLM trifft finale Entscheidung
  (analog zur bestehenden Orwell-Index-Kalibrierung)
- Geeignet für: Techniken, die Bezug zwischen benachbarten Sätzen brauchen
  (z. B. Whataboutism: Kritik + Ablenkung oft über mehrere Sätze verteilt)
- Kostenprofil: LLM-Call pro Fenster, aber Fensteranzahl deutlich kleiner als Satzanzahl

### Klasse 3 – Artikelebene (voller LLM)

- Granularität: gesamter Artikel
- Methode: bestehender Multi-Pass-Ansatz, voller LLM-Call
- Geeignet für: Techniken, die sich erst über den gesamten Text ergeben
  (z. B. Wiederholungsmuster, False Balance, Framing durch Häufung)
- Kostenprofil: teuerster Lauf, aber notwendig für kontextabhängige Techniken

## Wichtiges Architekturprinzip: keine sequenzielle Filterung

Die drei Läufe arbeiten **unabhängig und parallel**, nicht gestaffelt als Vorfilter/Feinprüfung.
Ein Satz, der Basis für eine Klasse-1-Erkennung ist, bleibt unverändert Teil der Klasse-2- und
Klasse-3-Läufe. Kein Aussieben von Sätzen zwischen den Klassen – jede Klasse sieht den vollen
Text unabhängig von den Ergebnissen der anderen Klassen.

## Zusammenführung: Dedup über (Technik, Zitat)-Tupel

Da Belege ohnehin als Zitate gespeichert werden, ist die Zusammenführung der drei Lauf-Ergebnisse
ein einfacher Uniqueness-Constraint:

- Schlüssel: Tupel aus **(Technik, Zitat)**
- Exakt gleiches Zitat + gleiche Technik aus zwei oder drei Läufen → eine Instanz
- Unterschiedliche Zitate (auch bei gleicher Technik) → separate Instanzen, korrekt gezählt

Kein Positions-Overlap-Vergleich, kein Granularitätsabgleich zwischen den Klassen nötig – das
Tupel-Dedup reicht aus, weil Klasse 2 grundsätzlich nicht auf Einzelsatzebene, sondern auf
Fenster-Ebene erkennt und somit keine Kollision mit Klasse-1-Belegen auf Satzebene entsteht.

## Umgang mit Streuung im Embedding-Raum: Thema als zusätzliche Dimension

Falls eine Technik im Embedding-Raum zu breit streut, um sie als eine kompakte Klasse zu
behandeln (Analogie: Multi-Cluster-Ansatz beim Clustern von Schriftzeichen bei zu großer
Streuung), wird das Thema als zweite Dimension neben der Technik mitgeführt – statt reiner
Technik-Cluster also (Technik × Thema)-Cluster.

- **Thema aus bestehender Pipeline-Klassifikation übernehmen**: Artikel werden bereits einer
  Themenkategorie zugeordnet, diese bestehende Zuordnung wird als zusätzliches Metadata-Feld
  `thema` neben `technik` und `zitat` in Chroma abgelegt – keine zusätzliche
  Themen-Klassifikation nötig
- **Suche**: NN-Suche berücksichtigt Thema als Gewichtung, nicht als reines Ausschlusskriterium
  – vermeidet, dass Cross-Themen-Signal (gleiche Technik, anderes Thema) komplett verloren geht

## Fallback bei fehlendem NN-Treffer

Analog zur bestehenden Orwell-Index-Kalibrierung (Ankerbeispiele + LLM-Call): Wenn die
NN-Suche in Chroma keinen ausreichend nahen Treffer liefert (weil eine Technik in einer
bestimmten Themenkategorie noch nicht durch Referenzbeispiele abgedeckt ist – Kaltstart-Fall),
übernimmt automatisch ein LLM-Call mit spezialisiertem Aufgabenprompt die Bewertung, ohne
(oder mit schwächeren, themenübergreifenden) Ankerbeispielen.

- Löst das Kaltstart-Problem, ohne dass Chroma vorab lückenlos für alle
  (Technik × Thema)-Kombinationen befüllt sein muss
- Referenzmenge wächst organisch: vom LLM-Fallback erfolgreich erkannte und verifizierte Fälle
  (über den Writer/Critic-Normalisierungs-Loop) fließen zurück in Chroma und schließen die
  Lücke für künftige Läufe

## Offene Punkte für die Umsetzung

1. **Technik → Klassen-Zuordnung** erstellen: welche Techniken sind Klasse 1, 2, 3 oder
   Kombinationen davon
2. **Distanz-Schwellenwert für Klasse 1** kalibrieren (Symmetrietest-Methodik) – bestimmt auch,
   wann der Kaltstart-Fallback greift
3. **Chunk-/Fenstergröße für Klasse 2** festlegen (Anzahl Sätze, Overlap-Grad)
4. **Embedding-Modell prüfen**, ob es strukturelle/rhetorische statt nur thematische Nähe
   abbildet – Testfall: zwei thematisch verschiedene, aber technisch identische Zitate sollten
   sich im Embedding-Raum nah kommen. Chroma-Default (`all-MiniLM-L6-v2`) ist auf semantische
   Ähnlichkeit optimiert und damit für diesen Zweck ungeeignet. Kandidat:
   `paraphrase-multilingual-mpnet-base-v2` (multilingual, paraphrastische statt thematische
   Ähnlichkeit, geeignet für deutschsprachige Artikel). Muss empirisch gegen den Testfall
   validiert werden, bevor das Modell festgelegt wird
5. **Referenzbeispiel-Pflege in Chroma**: Prozess definieren, wie neue verifizierte Beispiele
   (aus dem Writer/Critic-Normalisierungs-Loop) laufend eingepflegt werden, inklusive Rückfluss
   aus dem LLM-Fallback
