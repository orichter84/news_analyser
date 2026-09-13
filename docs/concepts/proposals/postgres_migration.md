# Konzeptentwurf: ChromaDB ablösen — PostgreSQL/pgvector oder leichtgewichtige Alternativen

**Status:** Nicht entschieden. Zurückgestellt, bis feststeht, ob die eigentliche Ursache der
ChromaDB-Abstürze auf dem Server (siehe unten) tatsächlich für eine Migration spricht.

## Ausgangslage

Am 27.08.2026 ist der ChromaDB-Dienst auf dem Server ohne Fehlermeldung abgestürzt. Ursache
unklar, da zu dem Zeitpunkt keine Logs persistiert wurden (`start.sh` leitete die
Prozess-Ausgabe nirgendwo um). Ein einfacher Neustart hat den Dienst sofort wieder
funktionsfähig gemacht — spricht eher für ein einmaliges Ereignis (OOM-Kill, abgerissene
SSH-Session) als für einen reproduzierbaren Bug, ist aber ohne Log nicht sicher zu klären.

Als direkte Konsequenz wurde `start.sh` so angepasst, dass alle drei Dienste (ChromaDB,
Backend, Frontend) ihre Ausgabe nach `logs/*.log` umleiten, und die Systemstatus-Seite
(`/system`) zeigt diese Logs jetzt live im Frontend an. Tritt der Absturz erneut auf, gibt es
damit erstmals eine Fehlerursache zum Auswerten.

Unabhängig davon entstand aus einer Diskussion mit ChatGPT die Idee, ChromaDB grundsätzlich
durch PostgreSQL mit der `pgvector`-Extension zu ersetzen. Dieses Dokument hält die
Kernpunkte dieser Diskussion sowie eine Aufwands-/Nutzen-Einschätzung fest, damit die
Entscheidung getroffen werden kann, sobald klar ist, woran ChromaDB tatsächlich gescheitert
ist.

## Aktuelle Architektur (zur Einordnung)

ChromaDB übernimmt im Projekt aktuell zwei unterschiedliche Rollen, die in einem
Migrationsszenario getrennt betrachtet werden müssen:

1. **Strukturierte Artikel-Ablage** (`repositories/db_storage.py`): Artikel samt allen
   Kennzahlen (Orwell-Index, Bernays Score, DK-Index, Domain, Themenbereich, …) werden als
   Chroma-Metadata gespeichert. `stats.py` liest dafür **alle** Datensätze aus Chroma, baut
   daraus einen pandas-DataFrame und aggregiert dort (Top-Techniken, Domain-Durchschnitte,
   Themenbereichs-Auswertung usw.) — weil Chroma selbst keine GROUP-BY-/Aggregat-Queries kann.
2. **Semantische Ähnlichkeitssuche** (`repositories/anchor_store.py`,
   `repositories/technique_store.py`, `repositories/role_store.py`): Nearest-Neighbor-Suche
   gegen Referenzbeispiele — die eigentliche Stärke einer Vektordatenbank, hier tatsächlich
   genutzt.

Punkt 1 ist der eigentliche Schmerzpunkt: Chroma wird hier wie eine relationale Datenbank
benutzt, kann aber keine echten Aggregat-Queries — das SQL-Argument aus der ChatGPT-Diskussion
trifft also zu.

## Vorschlag aus der Diskussion: PostgreSQL + pgvector

**Stack:** PostgreSQL 15+, `pgvector`-Extension (Index-Typen `HNSW` oder `IVFFlat`,
Distanzmaße Cosine/Inner-Product/L2), Python-seitig `psycopg3` oder `SQLAlchemy 2.0+`.

Schema-Skizze:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536), -- an Embedding-Modell anpassen (z.B. 384/768/1536)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON document_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

Vektorsuche und Hybrid-Filterung (Metadata + Ähnlichkeit) in einer einzigen Query:

```sql
SELECT id, content, metadata, 1 - (embedding <=> :query_vector) AS similarity
FROM document_embeddings
ORDER BY embedding <=> :query_vector
LIMIT :top_k;
```

Migrationsschritte: PostgreSQL + pgvector aufsetzen, Vektor-Dimension festlegen, bestehende
Chroma-Collections exportieren (IDs, Embeddings, Metadata), Metadata-Felder auf JSONB oder
eigene Spalten abbilden, Bulk-Insert, HNSW-Index erst **nach** dem initialen Laden erstellen
(schnellerer Build), danach Top-K-Recall und Latenz gegen die bisherige Chroma-Lösung
validieren.

## Aufwands- und Nutzenabschätzung

**Für eine Migration spricht:**
- Echtes SQL für `stats.py` statt Pandas-Aggregation über den kompletten Datenbestand bei
  jedem Report — der eigentlich saubere Fix für den oben beschriebenen Schmerzpunkt.
- Deutlich reifere Betriebs-/Diagnosewerkzeuge (echte Logs, `pg_ctl status`,
  WAL-basierte Crash-Recovery, `pg_dump`) — relevant, falls sich der Chroma-Absturz als
  strukturelles Zuverlässigkeitsproblem herausstellt.
- ACID-Transaktionen, falls perspektivisch mehrere Schreiber gleichzeitig auf die Daten
  zugreifen sollen.

**Dagegen spricht:**
- Kein kleiner Umbau — betrifft praktisch die gesamte Repository-Schicht
  (`chroma_client.py`, `db_storage.py`, `anchor_store.py`, `technique_store.py`,
  `role_store.py`) plus `stats.py`.
- PostgreSQL muss selbst als eigener Dienst laufen und gewartet werden — auf dem
  Mac-Mini-Server kommt damit ein zusätzlicher Dienst zum Betreuen dazu, nicht weniger. Löst
  das ursprüngliche "Dienst crasht" Problem also nicht per se, verschiebt es nur auf eine
  (vermutlich robustere) andere Datenbank.
- Der Skalierungsvorteil von pgvector (HNSW bei Millionen Vektoren) löst ein Problem, das
  dieses Projekt bei aktuell einigen Dutzend Artikeln nicht hat.

**Einschätzung:** Der SQL-Aggregations-Vorteil ist real, aber die Server-Betriebslast von
PostgreSQL ist bei dieser Datenmenge unverhältnismäßig zum Nutzen. Eine vollständige
Postgres-Migration lohnt sich eher, falls die Datenmenge deutlich wächst oder mehrere
gleichzeitige Schreiber hinzukommen.

## Leichtgewichtigere Alternativen

Beide lösen das eigentliche Problem (fehlende SQL-Aggregation) ohne einen zusätzlichen
Dienst einzuführen — sie sind wie ChromaDB eingebettet, es gibt also nichts Neues, das
abstürzen kann:

- **SQLite + [`sqlite-vec`](https://github.com/asg017/sqlite-vec)**: eingebettet wie Chroma
  jetzt, aber echtes SQL (inkl. GROUP BY/JOIN) für `stats.py`, plus eine einfache
  Vektorsuche-Extension für die Anchor-/Technique-Stores. Migration betrifft dieselben Dateien
  wie bei Postgres, aber ohne neuen Serverprozess.
- **DuckDB + VSS-Extension**: ähnlich eingebettet, zusätzlich von Haus aus für genau solche
  Analytics-/Reporting-Workloads ausgelegt wie die `stats.py`-Auswertungen (spaltenorientiert,
  schnelle Aggregate über große Datenmengen).

Beide wären ein deutlich kleinerer Schnitt als die vollständige Postgres-Migration und ein
naheliegender Zwischenschritt, falls sich zeigt, dass primär die Pandas-Aggregation in
`stats.py` der Schmerzpunkt ist — unabhängig davon, ob sich ChromaDBs Zuverlässigkeit als
Problem bestätigt.

## Entscheidungskriterium

Die Wahl hängt von der tatsächlichen Ursache eines erneuten ChromaDB-Absturzes ab (jetzt über
`logs/chroma.log` bzw. die Systemstatus-Seite einsehbar):

- **Zuverlässigkeits-/Crash-Problem** (z.B. wiederkehrender Absturz, Speicherleck) → eher
  PostgreSQL, da hier die operative Reife den Ausschlag gibt.
- **Kein wiederkehrendes Problem, primär Unzufriedenheit mit der Stats-Query-Umständlichkeit**
  → eher SQLite+`sqlite-vec` oder DuckDB, da der eigentliche Schmerzpunkt (SQL-Aggregation)
  ohne zusätzlichen Betriebsaufwand gelöst wird.

## Offene Punkte für die Umsetzung

1. **Ursachenklärung abwarten**: nächsten ChromaDB-Ausfall (falls es einen gibt) anhand der
   jetzt vorhandenen Logs auswerten, bevor eine Variante festgelegt wird.
2. **Vektor-Dimension und Embedding-Modell** für die Ziel-Lösung festlegen (aktuell
   `paraphrase-multilingual-MiniLM-L12-v2`, 384 Dimensionen).
3. **Migrationsskript** für die drei bestehenden Collections (`articles`, `orwell_anchors`,
   `techniques`) entwerfen, inkl. Mapping der Chroma-Metadata-Felder.
4. **Recall-/Latenz-Vergleich** der Vektorsuche zwischen aktueller Chroma-Lösung und
   Zielsystem, bevor produktiv umgestellt wird.
5. **Deployment-Doku aktualisieren** (`start.sh`, `SETUP.md`, `.env.example`) für den
   gewählten Ansatz — bei Postgres zusätzlich Backup-/Restore-Strategie festlegen.
