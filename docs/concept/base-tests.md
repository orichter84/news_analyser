# Test Results — First Proof of Concept

**Date:** 22 May 2026  
**System:** news_analyser v0.1 — CLIAdapter (claude-sonnet-4-6)  
**Metric:** Orwell Index (−1.0 to +1.0)

---

## Methodological Notes

### Source selection and inherent bias

The selection of test sources is itself an act with bias potential and must be made transparent as such.

Sources were deliberately chosen for **ideological breadth** — from verified historical propaganda texts through public broadcasters to explicitly positioned modern sources. The goal was not a representative cross-section of the German media landscape, but a **calibration test** of the analysis system across as wide a range of the political spectrum as possible.

The following biases are consciously present in the selection:

- **Thematic concentration**: Many articles cover the Lina E. case — a politically highly charged topic that pushes sources towards more extreme statements than routine reporting. Results are therefore not necessarily representative of a source's overall output.
- **Sample size**: At most one article per source was analysed. Reliable statements about an editorial team require significantly more data points.
- **Blind selection**: The tester deliberately did not read the articles before analysis to reduce their own confirmation bias. However, the source was known, which may have influenced selection.
- **Historical texts as anchors**: The NS and GDR texts serve as calibration points for known extremes, not as a direct comparison with modern journalism.

---

## The Orwell Index — Explanation

The Orwell Index is a floating-point number between **−1.0** and **+1.0** assigned by the LLM agent. It measures the **ideological orientation** of a text, not its journalistic quality.

### Scale

| Range | Meaning |
|---|---|
| `−1.0 to −0.6` | Strongly left-liberal / progressive |
| `−0.6 to −0.2` | Left-liberal |
| `−0.2 to +0.2` | Largely neutral |
| `+0.2 to +0.6` | Right-conservative |
| `+0.6 to +1.0` | Strongly right-conservative / nationalist |

### What the score measures

The score evaluates *which direction* the rhetorical devices of a text point — which actors, positions or narratives are valorised (+) or devalued (−). It is **not a quality judgement**: a well-crafted article can have a high score, a poorly researched one a low score.

### What the score does not measure

- **Factual accuracy**: A factually correct article can be strongly framed.
- **Journalistic rigour**: Source selection, research and balance do not factor in directly.
- **Absolute neutrality**: A score near 0.0 does not mean absence of perspective, but that the rhetorical devices balance each other out.

### How the score is produced

The agent evaluates the text holistically based on detected techniques, language, selection and weighting of facts, and implicit narratives. It is an **LLM estimate**, not a mathematically derivable metric — reproducibility is high but not absolute. Repeated analyses of the same article can vary by ±0.1.

### Calibration points from this test

| Reference | Score | Meaning |
|---|---|---|
| NS Civil Service Act 1933 | `+0.97` | Theoretical maximum — state propaganda |
| GDR Construction Act 1950 | `−0.95` | Theoretical minimum — state propaganda |
| Wikipedia (Lina E.) | `+0.20` | Practical neutrality for editorially reviewed content |

---

## The Dunning-Kruger Index — Explanation

The Dunning-Kruger Index is a floating-point number between **0.0** and **1.0** assigned by the LLM agent. It measures the **epistemic confidence** of a text — how assertively claims are made relative to the evidential basis.

### Scale

| Range | Meaning |
|---|---|
| `0.0 to 0.3` | Epistemically humble — statements qualified, sources cited, uncertainty acknowledged |
| `0.3 to 0.6` | Moderately confident — mixed hedges and certainty statements |
| `0.6 to 1.0` | Epistemically overconfident — definitive claims without backing |

### What the index measures

The index evaluates the ratio between the **certainty** with which claims are made and their **evidential basis**. High values arise from: definitive formulations without citations, missing hedges ("could", "according to", "possibly"), ignoring counterarguments, and denial of complexity.

### What the index does not measure

- **Factual accuracy**: A factually correct text can score high, a false one low.
- **Ideological direction**: The index is orthogonal to the Orwell Index — any political direction can argue humbly or arrogantly.
- **Journalistic quality**: Factual reports can score low without being particularly good journalism.

### Calibration points from this test

| Reference | DK Index | Meaning |
|---|---|---|
| NS Civil Service Act 1933 | `0.92` | State propaganda with absolute claim to certainty |
| danisch.de | `0.92` | Opinion blog — theses without systematic evidence |
| Wikipedia (Lina E.) | `0.12` | Editorially reviewed, heavily qualified |
| MDR (Höcke/election) | `0.12` | Pure factual reporting (election results) |

---

## Phase 1 — Source Overview: Different Sources, Similar Topic

### Test design
First functional test with thematically related articles on NATO and international politics.

| Source | Article | Orwell Index | Techniques (count) |
|---|---|---|---|
| t-online.de | NATO foreign ministers meet in Sweden | `−0.55` | 6 |
| danisch.de | Mafia crisis Angstpublica | `+0.93` | 9 |

### Observations
- The system correctly identifies both poles without detectable self-bias.
- danisch.de is stylistically not a classic news outlet but an opinion blog — the high technique density (9) reflects the commentating, polemical style.
- Both sources use the same basic toolkit: FUD, loaded language, framing, emotional manipulation — just with opposite signs.

---

## Phase 2 — Public Broadcasters: ARD vs. MDR

### Test design
Comparison of national (Tagesschau/ARD) and regional (MDR) public broadcasters, initially with foreign policy topics.

| Source | Article | Orwell Index | Techniques |
|---|---|---|---|
| Tagesschau (ARD) | USA voting rights & civil rights | `−0.75` | 9 |
| MDR | Ukraine/NATO/Trump | `−0.25` | 5 |

### Observations
- MDR is significantly closer to zero than Tagesschau — both in score and technique density.
- The hypothesis "regional public broadcasters are more moderate" receives initial support.

---

## Phase 3 — MDR Internally: Political Topic Dependency

### Test design
Four MDR articles on politically differently charged topics, to test whether the score fluctuates by topic or is editorially stable.

| MDR article | Topic | Orwell Index | Techniques |
|---|---|---|---|
| Ukraine/NATO | Foreign policy (neutral) | `−0.25` | 5 |
| Mario Voigt/plagiarism | CDU politician | `−0.30` | 6 |
| Cultural funding act SA | AfD-relevant topic | `−0.45` | 6 |
| Björn Höcke/state election | AfD election result | `−0.20` | 3 |

### Observations
- MDR shows remarkable **consistency** — all scores fall between −0.20 and −0.45.
- The Höcke article is the most neutral — probably because pure election result reporting leaves little room for framing (numbers are numbers).
- A slight increase for the AfD-relevant cultural topic (−0.45) is visible but statistically not significant.
- **Conclusion**: MDR scores point to editorial culture, not topic-dependent framing.

---

## Phase 4 — The Spectrum: Same Topic, All Sources

### Test design
The politically maximally charged topic "Lina E." was analysed across all source types — from far-left to right-conservative — to map the full ideological axis. Supplemented by Wikipedia as a neutrality control group.

| Source | Camp | Orwell Index | Techniques |
|---|---|---|---|
| nd-aktuell | Far-left | `−0.82` | 8 |
| Tagesschau | Public broadcaster / left-liberal | `+0.25`* | 5 |
| MDR Podcast | Public broadcaster / regional | `−0.35` | 4 |
| MDR report | Public broadcaster / regional | `+0.30` | 2 |
| **Wikipedia** | **Neutral (control group)** | **`+0.15`** | **3** |
| Junge Freiheit | Right-conservative | `+0.85` | 7 |

*Tagesschau investigative article on Lina E., not identical format

### Observations
- **Near-perfect symmetry**: nd-aktuell at −0.82, Junge Freiheit at +0.85 — both extremes deliver similar technique densities (7–8).
- **Wikipedia passes the neutrality test**: +0.15 with 3 techniques from 69,000 characters of text is the strongest signal for system validity in this test.
- **Tagesschau anomaly**: The investigative Lina E. article (+0.25) deviates significantly from the Tagesschau foreign policy article (−0.75) — indicating that format and authorship vary more within an editorial team than between teams.
- **Core finding**: All sources use the same rhetorical toolkit. The Orwell Index measures the direction, not the existence of framing.

---

## Phase 5 — Historical Calibration

### Test design
Two historical propaganda texts with known ideological classification as anchors for the extreme points of the scale.

| Source | Era | Camp | Orwell Index | Techniques |
|---|---|---|---|---|
| Law for the Restoration of the Professional Civil Service | NS 1933 | Far-right | `+1.00` | 7 |
| GDR Construction Act (preamble) | SED 1950 | Far-left | `−0.92` | 7 |

### Observations
- The NS act reaches the **theoretical maximum of +1.00** — an important calibration point.
- The GDR Construction Act lands symmetrically at −0.92 and confirms the scale at both ends.
- **Identical technique density** (7 in both): historical state propaganda barely differs in *intensity* from modern extreme sources (JF: 7, nd: 8) — only the veneer is missing.
- The **rhetorical kinship** between early SED propaganda and NS rhetoric is reflected in the result: both use scapegoating, loaded language and emotional manipulation as core tools.

---

## Overall Summary

| Source | Orwell Index | Bernays Score | DK Index |
|---|---|---|---|
| NS Civil Service Act 1933 | `+0.97` | 4.49 | **0.92** |
| danisch.de | `+0.88` | 8.93 | **0.92** |
| GDR Construction Act 1950 | `−0.95` | 6.22 | **0.88** |
| Junge Freiheit | `+0.75` | 15.54 | 0.72 |
| nd-aktuell | `−0.85` | 10.57 | 0.72 |
| Tagesschau (USA voting rights) | `−0.65` | 6.00 | 0.62 |
| t-online.de | `−0.55` | 15.43 | 0.62 |
| MDR (Voigt/plagiarism) | `−0.30` | 5.01 | 0.55 |
| MDR (cultural funding) | `−0.45` | 6.08 | 0.30 |
| MDR (Lina E. podcast) | `−0.45` | 8.47 | 0.25 |
| MDR (Lina E. release) | `+0.30` | 6.06 | 0.25 |
| MDR (Ukraine/NATO) | `−0.30` | 2.39 | 0.20 |
| Tagesschau (Lina E. investigative) | `+0.28` | 5.51 | 0.22 |
| **Wikipedia** | **`+0.20`** | **0.40** | **0.12** |
| MDR (Höcke/election) | `−0.25` | 3.29 | **0.12** |

---

## Conclusions

### What the results mean

**1. The system works and is consistent.**  
Wikipedia as a known neutrality control group lands near zero, historical state propaganda at the extremes. This gives credibility to the prompt design and the model.

**2. Framing is universal — direction is variable.**  
All tested sources, from nd-aktuell to Junge Freiheit, use the same rhetorical toolkit (loaded language, framing, emotional manipulation). The Orwell Index does not measure *whether* framing occurs, but *which direction* it points. Neutral reporting is the exception, not the rule.

**3. Public broadcasters are not neutral, but more moderate.**  
MDR and Tagesschau consistently land in the negative (left-liberal) range, but clearly distant from the ideological extremes. Their public funding and neutrality mandate are reflected in more moderate scores — but not in the absence of framing.

**4. Format and authorship vary more than editorial culture.**  
The strongest Tagesschau outlier came not from a different source, but from a different format (investigative vs. news report). A single article is not a reliable picture of an editorial team.

**5. The rhetorical DNA of the modern media landscape predates the internet.**  
Edward Bernays codified the tools in the 1920s. The NS and SED regimes perfected them. The scores of the historical texts (+1.00 / −0.92) are only marginally higher than the modern extreme sources (+0.93 / −0.82) — the toolkit has not changed, only the social context in which it is deployed.

---

## Limitations and Next Steps

- **n=1 per source**: Reliable statements require at least 20–50 articles per source.
- **Topic bias**: "Lina E." is an exceptional case. Routine reporting would likely produce more moderate scores.
- **Model bias**: The analysis agent (Claude) has its own training-data-based worldview. Systemic biases in the model can influence scores.
- **Missing counter-check**: No test with a clearly far-right source as a counterpart to nd-aktuell on the left (Compact would be the obvious choice).

The next sensible step is running the RSS feed collector for several weeks to reach a statistically meaningful sample size per source.

---

## Further Tests

The point mentioned under "Model bias" was subsequently investigated systematically.
The results of the bias validation and the resulting architectural decisions
(Orwell Index refactoring, two-pass anonymisation) are documented in:

**`docs/concept/bias-validation.md`**
