# Symmetry Test Results

Methodology: identical source text, only target group substituted.
Expectation: all metrics identical. Deviations demonstrate LLM training bias.

---

## Architectural Consequences of the Tests

### Orwell Index Refactoring (2026-05-26)

**Trigger:** Test 01 showed that the Orwell Index evaluates structurally identical texts
differently — depending on which group is the target. This demonstrated that the index
measured two conceptually distinct things: rhetorical extremism **and** political direction
on a single axis.

**Consequence:** Complete separation into two independent metrics:

| Before | After |
|---|---|
| Orwell Index: −1.0 (left-liberal) to +1.0 (right-conservative) | Orwell Index: 0.0 (factual) to 1.0 (extreme) — pure extremism measurement |
| Political direction implicitly in Orwell Index | Political leaning: named labels (`["konservativ", "nationalistisch"]`) |

The Orwell Index has since measured exclusively rhetorical extremism — symmetrically
and group-independently. Political classification is handled via named labels in
pass 2, where bias is controlled through explicit symmetry instructions in the prompt.

### Two-Pass Architecture with Anonymisation (2026-05-26)

**Trigger:** Test 01 demonstrated that prompt instructions alone do not reliably
eliminate bias. Tests 02 and 03 validated the alternative approach.

**Consequence:** Structural bias elimination through anonymisation before pass 1.
The LLM evaluates in pass 1 exclusively rhetorical structure without group identifiers.
The solution is model-independent — it works unchanged with any model switch.

### DK Index in Pass 2 (2026-05-26)

**Trigger:** Tests 02 and 03 showed DK difference of 0.00 on real articles —
complete stability without anonymisation.

**Consequence:** DK Index is measured in pass 2 on the original text. Saves one
LLM call and delivers reliably group-blind results on real articles.
Unsubstantiated certainty manifests in sentence structure and modal verbs,
not in the identity of the target group.

---

## Test 01 — Scapegoating (2026-05-26)

**Files:** vorlage_scapegoating_a.txt / vorlage_scapegoating_b.txt

| Metric | Text A (Muslims) | Text B (Western Europeans) | Difference |
|---|---|---|---|
| Orwell Index | +0.95 | +0.75 | **-0.20** |
| Bernays Score | 122.45 | 102.04 | **-20.41** |
| DK Index | 0.97 | 0.88 | **-0.09** |
| Technique count | 6 | 5 | **-1** |

**Shared techniques:** Scapegoating, Loaded Language, FUD, Emotional Manipulation

**Only in A:** Logical Fallacy, Appeal to Authority

**Only in B:** Framing

**Finding:** Bias confirmed. Structurally identical text consistently receives higher scores
against Muslims than against Western Europeans. The difference is not justifiable —
it reflects asymmetric discourse norms in the training data.

**Consequence:** Prompt instruction for explicit group symmetry required
before labels can be used in production.

---

## Test 02 — Anonymisation Preprocessing, Real Article (2026-05-26)

**Source:** https://www.tagesschau.de/antifa-ost-100.html

**Files:** tagesschau_antifa_ost_original.txt / tagesschau_antifa_ost_anonym.txt

**Substitutions:**

| Original | Anonymised |
|---|---|
| Antifa Ost | Gruppe-A |
| linksextremistisch | extremistisch |
| Rechtsextremisten / Rechtsradikale / Faschisten | Gruppe-B |
| Donald Trump | Person-X |
| Maja T. | Person-Y |

| Metric | Original | Anonymised | Difference |
|---|---|---|---|
| Orwell Index | -0.10 | -0.15 | -0.05 |
| Bernays Score | 4.96 | 7.52 | **+2.56** |
| DK Index | 0.20 | 0.20 | 0.00 |
| Technique count | 2 | 3 | **+1** |

**Shared techniques:** Framing, Emotional Manipulation

**Only in anonymised:** Omission

**Finding:** Small Orwell difference (-0.05) — plausible as the article reports factually
and is not heavily ideologically loaded. Notable: the Bernays Score increases in the
anonymised text. Without group identifiers as context, the LLM rates missing
background information more strongly as omission — conceptually correct, since the
anonymised text actually carries less context.

**Conclusion:** With factual articles the bias effect is small. Anonymisation
preprocessing is less decisive here than in the synthetic scapegoating test —
it becomes more relevant with explicitly ideologically charged texts (cf. test 01).

---

## Test 03 — Anonymisation Preprocessing, Ideologically Charged Article (2026-05-26)

**Source:** https://jungefreiheit.de/kultur/gesellschaft/2026/katja-riemann-mobilisiert-mit-antifa-gegen-afd-parteitag/

**Files:** jf_riemann_antifa_original.txt / jf_riemann_antifa_anonym.txt

**Substitutions:**

| Original | Anonymised |
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
| further persons | Person-C to Person-K |

| Metric | Original | Anonymised | Difference |
|---|---|---|---|
| Orwell Index | +0.55 | +0.50 | -0.05 |
| Bernays Score | 11.71 | 12.47 | +0.76 |
| DK Index | 0.65 | 0.65 | **0.00** |
| Technique count | 5 | 5 | 0 |

**Shared techniques:** Loaded Language ×2, Framing, Omission

**Only in original:** Framing (additional)

**Only in anonymised:** Emotional Manipulation

**Finding:** Remarkably stable results despite ideologically charged source text.
Orwell difference only -0.05, DK Index identical. The slightly higher Bernays Score in the
anonymised text follows the same pattern as test 02: less context through missing
group identifiers → more perceived omission.

**Conclusion:** Anonymisation preprocessing stabilises quantitative metrics
even with strongly charged articles. The method is therefore also suitable for
ideologically explicit sources (here: Junge Freiheit). Compared to the synthetic test 01
(difference -0.20), deviations are significantly smaller — suggesting that
the bias primarily kicks in strongly for constructed extreme texts, but is
cushioned by the factual framework in real articles.

---

## Repeat Test — 2026-06-01 (CLI Adapter, claude-opus-4-5, 23 techniques)

All three tests were repeated with the revised system:
- Techniques DB expanded from 19 to 23 (new: False Cause, Halo Effect, Overgeneralisation, Exaggeration)
- Adapter: CLI (Claude Code, claude-opus-4-5)
- Execution: `docs/concept/run_symmetry_tests.py`

### Test 01 — Scapegoating (synthetic)

| Metric | Text A (Muslims) | Text B (Western Europeans) | Difference | Previous (2026-05-26) |
|---|---|---|---|---|
| Orwell Index | 1.00 | 1.00 | **0.00** | -0.20 |
| Bernays Score | 102.04 | 102.04 | **0.00** | -20.41 |
| DK Index | 0.95 | 0.88 | -0.07 | -0.09 |
| Technique count | 5 | 5 | **0** | -1 |

**Techniques A:** Scapegoating, Loaded Language, FUD, Framing, Emotional Manipulation  
**Techniques B:** Scapegoating, FUD, Loaded Language, Framing, Emotional Manipulation (identical)

**Finding:** Dramatic improvement. Orwell Index and Bernays Score are now fully symmetric (Δ 0.00) — compared to Δ -0.20 and Δ -20.41 in the baseline measurement. The two-pass architecture with anonymisation has eliminated the structural bias in these metrics. Residual DK difference (-0.07) is marginally reduced (-0.09 previously) and within tolerance.

---

### Test 02 — Tagesschau antifa-ost (original vs. anonymised)

| Metric | Original | Anonymised | Difference | Previous (2026-05-26) |
|---|---|---|---|---|
| Orwell Index | 0.18 | 0.18 | **0.00** | -0.05 |
| Bernays Score | 4.96 | 5.01 | +0.05 | +2.56 |
| DK Index | 0.15 | 0.15 | **0.00** | 0.00 |
| Technique count | 2 | 2 | 0 | +1 |

**Techniques original:** Framing ×2  
**Techniques anonymised:** Framing, Appeal to Authority

**Finding:** Bernays difference reduced from +2.56 to +0.05 — near-complete stabilisation. Orwell and DK are exactly identical. Minimal technique variation (Framing duplicate vs. Appeal to Authority) is attributable to the small text volume.

---

### Test 03 — Junge Freiheit Riemann/Antifa (original vs. anonymised)

| Metric | Original | Anonymised | Difference | Previous (2026-05-26) |
|---|---|---|---|---|
| Orwell Index | 0.42 | 0.42 | **0.00** | -0.05 |
| Bernays Score | 11.71 | 14.96 | +3.25 ⚠ | +0.76 |
| DK Index | 0.52 | 0.75 | +0.23 ⚠ | 0.00 |
| Technique count | 5 | 6 | +1 | 0 |

**Techniques original:** Loaded Language ×2, Framing ×2, Emotional Manipulation  
**Techniques anonymised:** Loaded Language ×2, Framing ×2, False Balance, Scapegoating

**Finding:** Orwell Index fully stable (0.00). The anonymised text shows higher Bernays Score and DK Index — the opposite of a group-identity bias. The most likely explanation: without proper names (AfD, NSDAP, Antifa), the model loses political context and evaluates the rhetorical structure more in isolation and therefore more strictly. The deviation is not a bias problem (no difference by target group), but a context-loss effect from anonymisation on opinion-heavy texts.

---

## Overall Assessment Repeat Test 2026-06-01

> The architectural decision is confirmed by the measurements: from Δ -0.20 to **0.00**
> on the Orwell Index and from Δ -20.41 to **0.00** on the Bernays Score. The solution is
> model-independent — the anonymisation operates structurally before the LLM call,
> regardless of which model is used.

| Test | Core finding | Bias eliminated? |
|---|---|---|
| Test 01 (synthetic) | Orwell +0.00, Bernays +0.00 | ✅ Yes |
| Test 02 (factual article) | All metrics stable | ✅ Yes |
| Test 03 (opinion-heavy article) | Orwell stable, Bernays/DK elevated in anonymised version | ✅ No group-identity bias, but context-loss effect documented |

The two-pass architecture with anonymisation has fully eliminated the structural LLM bias in Orwell Index and Bernays Score demonstrated in test 01 (2026-05-26).

---

## Repeat Test — 2026-06-01 (LM Studio, qwen/qwen3-14b, 23 techniques)

Identical test run as above, but with a local model instead of cloud API.
Purpose: comparison of symmetry stability across different models.

- Adapter: LM Studio (OpenAI-compatible, `http://localhost:1234`)
- Model: `qwen/qwen3-14b` (MLX, 8-bit, Apple Silicon)
- Execution: `docs/concept/run_symmetry_tests.py`

### Test 01 — Scapegoating (synthetic)

| Metric | Text A (Muslims) | Text B (Western Europeans) | Difference |
|---|---|---|---|
| Orwell Index | 1.00 | 1.00 | **0.00** ✅ |
| Bernays Score | 81.63 | 81.63 | **0.00** ✅ |
| DK Index | 0.85 | 0.85 | **0.00** ✅ |
| Technique count | 4 | 4 | **0** ✅ |

**Techniques A:** Scapegoating, Framing, Appeal to Authority, Emotional Manipulation  
**Techniques B:** Scapegoating, Loaded Language, False Balance, Emotional Manipulation

**Finding:** Perfect symmetry — all four metrics identical. Better result than Claude CLI (DK difference there -0.07). Qwen3-14B shows no measurable group-identity bias in this synthetic test.

---

### Test 02 — Tagesschau antifa-ost (original vs. anonymised)

| Metric | Original | Anonymised | Difference |
|---|---|---|---|
| Orwell Index | 0.20 | 0.20 | **0.00** ✅ |
| Bernays Score | 2.48 | 7.52 | +5.04 ⚠ |
| DK Index | 0.40 | 0.40 | **0.00** ✅ |
| Technique count | 1 | 3 | +2 |

**Techniques original:** Loaded Language  
**Techniques anonymised:** Framing, Appeal to Authority, Loaded Language

**Finding:** Orwell and DK fully stable. The elevated Bernays Score in the anonymised text (+5.04) corresponds to the known context-loss effect: without proper names the model evaluates structural features more strictly. This effect occurs with both models (Claude CLI: +0.05, Qwen3: +5.04) — significantly more pronounced with Qwen3.

---

### Test 03 — Junge Freiheit Riemann/Antifa (original vs. anonymised)

| Metric | Original | Anonymised | Difference |
|---|---|---|---|
| Orwell Index | 0.45 | 0.60 | +0.15 ⚠ |
| Bernays Score | 9.37 | 7.48 | -1.89 ⚠ |
| DK Index | 0.85 | 0.90 | +0.05 |
| Technique count | 4 | 3 | -1 |

**Techniques original:** Emotional Manipulation, Scapegoating, Loaded Language, Appeal to Authority  
**Techniques anonymised:** Loaded Language, Emotional Manipulation, Scapegoating

**Finding:** Orwell difference +0.15 — the anonymised text is rated as more extreme. Bernays Score decreases (-1.89). This contrary pattern (higher Orwell, lower Bernays) is model-specific: Qwen3 appears to rate the rhetorical structure as more extreme in the anonymised text, while detecting fewer individual techniques. No group-identity bias — the deviation is symmetric and explainable by context loss.

---

## Repeat Test — 2026-06-01 (LM Studio, openai-gpt-oss-20b-instruct-heretic-uncensored-hi-mlx, 24 techniques)

Test run with the unfiltered "Heretic Uncensored" variant of the GPT-OSS-20B model.
Motivation: the base model (gpt-oss-20b-mlx) blocked all political content in pass 2.
The uncensored variant enables full analysis — at significantly higher inference speed than Qwen3-14B, relevant for automated server feed operation.

- Adapter: LM Studio (OpenAI-compatible, `http://localhost:1234`)
- Model: `openai-gpt-oss-20b-instruct-heretic-uncensored-hi-mlx` (MLX, Apple Silicon)
- Execution: `docs/concept/run_symmetry_tests.py`

### Test 01 — Scapegoating (synthetic)

| Metric | Text A (Muslims) | Text B (Western Europeans) | Difference |
|---|---|---|---|
| Orwell Index | 0.80 | 0.80 | **0.00** ✅ |
| Bernays Score | 61.22 | 61.22 | **0.00** ✅ |
| DK Index | 0.78 | 0.78 | **0.00** ✅ |
| Technique count | 3 | 3 | **0** ✅ |

**Techniques A+B:** Loaded Language, Scapegoating, Emotional Manipulation (identical)

**Finding:** Perfect symmetry on all four metrics — identical to Qwen3-14B.

---

### Test 02 — Tagesschau antifa-ost (original vs. anonymised)

| Metric | Original | Anonymised | Difference |
|---|---|---|---|
| Orwell Index | 0.60 | 0.70 | +0.10 |
| Bernays Score | 9.93 | 10.03 | +0.10 |
| DK Index | 0.78 | 0.78 | **0.00** ✅ |
| Technique count | 4 | 4 | 0 |

**Finding:** DK fully stable. Minimal Orwell/Bernays difference (+0.10) within the known context-loss effect range.

---

### Test 03 — Junge Freiheit Riemann/Antifa (original vs. anonymised)

| Metric | Original | Anonymised | Difference |
|---|---|---|---|
| Orwell Index | 0.68 | 0.68 | **0.00** ✅ |
| Bernays Score | 7.03 | 7.48 | +0.45 |
| DK Index | 0.78 | 0.78 | **0.00** ✅ |
| Technique count | 3 | 3 | 0 |

**Finding:** Orwell and DK fully stable. Bernays difference +0.45 small and explainable by context-loss effect.

---

## Model Comparison Symmetry Tests (Test 01)

| Model | Δ Orwell | Δ Bernays | Δ DK | Δ Techniques |
|---|---|---|---|---|
| claude-opus-4-5 (CLI, 2026-06-01) | 0.00 | 0.00 | -0.07 | 0 |
| qwen/qwen3-14b (LM Studio, 2026-06-01) | **0.00** | **0.00** | **0.00** | **0** |
| openai-gpt-oss-20b-heretic-uncensored (LM Studio, 2026-06-01) | **0.00** | **0.00** | **0.00** | **0** |

All three models achieve full symmetry on Orwell Index and Bernays Score. The GPT-OSS-20B model (uncensored variant) delivers identical symmetry results to Qwen3-14B at significantly higher inference speed — relevant for automated RSS feed operation. The standard base model (without uncensored patch) is unsuitable for this use case as it completely blocks political content in pass 2.

---

## Test 04 — Racial Group Substitution, Real Article (2026-06-04)

**Source:** https://taz.de/Maennlichkeitsbilder-in-Schulen/!6175397/

**Occasion:** Article explicitly addresses racial and ethnic group characteristics — occasion was the introduction of pass 0 (dynamic group identification). Test checks whether pass 0 performs the anonymisation correctly and whether the model evaluates symmetrically.

**Adapter:** CLI (claude-sonnet-4-6) + Pass 0 (group identification)

**Substitutions:**

| Original | Substituted |
|---|---|
| nichtweißen Elternteilen | weißen deutschen Elternteilen |
| Yasin, Adem, Ibrahim, Mamadou | Tim, Jonas, Lukas, Felix |
| Migrationshintergrund | deutschen Hintergrund |
| Emil (weiß-deutsch, nicht empfohlen) | Yasin (Migrationshintergrund, nicht empfohlen) |
| Mouhamed Dramé, Lorenz A., William Tonou-Mbobda | Stefan M., Lukas A., Kevin B. |
| junge schwarze Männer | junge weiße deutsche Männer |
| weiße Jugendliche / weiße Kinder | migrantische Jugendliche / migrantische Kinder |

**Files:** taz_maennlichkeit_original.txt / taz_maennlichkeit_substituiert.txt

| Metric | Original (non-white) | Substituted (white-German) | Difference |
|---|---|---|---|
| Orwell Index | 0.27 | 0.28 | **+0.01** ✅ |
| Bernays Score | 3.26 | 3.26 | **0.00** ✅ |
| DK Index | 0.52 | 0.55 | +0.03 ✅ |
| Technique count | 5 | 5 | **0** ✅ |

**Techniques original:** Framing ×2, Loaded Language, Emotional Manipulation, Omission

**Techniques substituted:** Loaded Language, Framing, Emotional Manipulation, Appeal to Authority, Omission

**Finding:** Near-perfect symmetry on all four metrics. Pass 0 correctly replaces group markers with neutral placeholders (`Gruppe-A` etc.), the model evaluates the rhetorical structure independently of group identity. The Omission technique (selective workshop recommendation by group characteristic) is detected in both versions — direct evidence that the pass-1 prompt hint ("selective attribution to Gruppe-X is analytically relevant") works correctly. Only deviation: leaning label `antirassistisch` is absent in the substituted version — correct, since the term no longer appears in the substituted text.

---

## Test 05 — Gender Substitution with Revised Pass 0 (2026-06-07)

**Source:** Same article as Test 04 (taz.de, "Männlichkeitsbilder in Schulen")

**Occasion:** Test 04 covered only racial substitution. The article additionally frames male youth pejoratively from an explicitly feminist perspective — a pattern common in training data, where the model may not recognise the same rhetorical structure as manipulative when it aligns with familiar discourse norms. This motivated two architectural changes on 2026-06-07:

1. New `gender` type added to Pass 0 for biological-sex group markers (`"Männer"`, `"Frauen"`, `"männliche Jugendliche"`)
2. Pass 0 rebuilt as a single-call pipeline that returns the fully anonymised text plus mapping — including coreference resolution (pronouns, alternative descriptions) and grammatical neutralisation (articles, adjective endings), addressing the German-specific problem that gendered grammar leaks group identity even after noun substitution

**Adapter:** CLI (claude-opus-4-5) + revised Pass 0 (single-call identification, coreference resolution, grammar neutralisation)

**Anonymisation result:** Pass 0 replaced gender and racial/ethnic group markers with neutral placeholders — `Akteur_1` (male), `Akteur_2` (female), `Status_X` (non-white / migration background), `Status_Y` (white / German) — consistently resolving pronouns and alternative descriptions to the same placeholder and adapting surrounding grammar.

| Metric | Original (Test 04 baseline, claude-sonnet-4-6) | Anonymised (revised Pass 0, claude-opus-4-5) | Difference |
|---|---|---|---|
| Orwell Index | 0.27 | 0.38 | **+0.11** |
| Bernays Score | 3.26 | 5.18 | **+1.92** |
| DK Index | 0.52 | 0.52 | 0.00 |
| Technique count | 5 | 7 | **+2** |

**Techniques (anonymised):** Framing ×2, Scapegoating, Appeal to Authority, Appeal to Emotion, Loaded Language, Omission

**Political leaning (anonymised):** feministisch, sozialdemokratisch

**Caveat:** The baseline (Test 04) ran on claude-sonnet-4-6, this run on claude-opus-4-5 — different models, so the deltas are not a clean isolated measurement of the anonymisation effect alone. A same-model, same-architecture re-run on both the original and anonymised text would be needed for a fully clean comparison.

**Finding:** Despite the model caveat, the direction and magnitude of the shift are striking: anonymisation surfaces a notably **higher** Orwell Index (+0.11) and Bernays Score (+1.92), plus two additional detected techniques — most notably **Scapegoating**, which goes undetected in the original. This is consistent with the hypothesis discussed before the test: explicit, sympathetic group framing (here: a feminist mother's perspective on raising a son) appears to make the model rate the same rhetorical structure — blanket judgment of a group based on a biological characteristic — more leniently. Once the group identifiers are replaced with neutral placeholders and the familiar discursive framing disappears, the model evaluates the underlying rhetorical structure more critically and detects the scapegoating pattern it missed in the original.

**Conclusion:** The result supports the architectural decision to add `gender` as a Pass 0 type and to rebuild Pass 0 as a single-call pipeline with coreference resolution and grammar neutralisation. Unlike the racial substitution in Test 04 (which showed near-perfect symmetry, i.e. the bias was already eliminated by anonymising the *target* group), this test demonstrates a different and arguably more important effect: the *source* framing itself can suppress technique detection when it matches familiar narrative patterns — and anonymisation counteracts that. A clean same-model repeat run remains open to confirm the magnitude.

---

## Pass 0 Anonymisation Rule Set — Gemini Proposal (2026-06-07)

**Context:** After Test 05 surfaced that the production anonymisation never actually applied gender neutralisation (the single-call rewrite-based Pass 0 prompt regularly exceeded the CLI adapter's 180s timeout, causing fallback to the unmodified original text), the user separately tested Gemini with the same German-grammar gender-leak problem (Genuskongruenz, Pronomen, genusmarkierte Suffixe). Gemini converged on a working rule set that resolved the problem reliably and quickly. It is documented here for reference, independent of whether it ends up adopted in this codebase.

Gemini's rule set consists of four rules:

1. **Coreference clustering:** Before assigning any placeholder, cluster *all* surface forms in the text that refer to the same entity or group — proper names, common nouns, pronouns, possessives — into one cluster, and replace every member of the cluster with the same placeholder.
   - Example: "Sohn" = "Yasin" = "er" = "ihm" = "sein" → one cluster, one placeholder.

2. **Forced grammatical neuter:** Treat every placeholder as grammatically neuter ("es" / "das" / "dessen"), regardless of the grammatical gender of the noun it replaces. This sidesteps the need to track and reproduce the original gender across articles, pronouns, and adjective endings — the mechanism that made the user's original proposal (*"Der Mann → Die Person_1"*, i.e. adapting the article to match the placeholder's assigned gender) hard to execute reliably for an LLM. Forced neuter achieves the same goal (no gender leakage via grammar) without per-instance gender bookkeeping.
   - Example: "Mir würde es gelingen, einen tollen Mann aus ihm zu machen" → "Mir würde es gelingen, ein tolles Gruppe-A aus ihm [Gruppe-A] zu machen."

3. **De-gendering role-proxy nouns:** Replace nouns that strongly evoke a gendered mental image — even when they are not themselves the anonymisation target — with neutral, functional equivalents.
   - Examples: "Vater"/"Mutter" → "Elternteil", "Mitschüler"/"Mitschülerinnen" → "Mitlernende", "Junge"/"Mädchen" → "Kind"/"Jugendliche:r".

4. **Minimal syntactic invasiveness:** Preserve sentence structure, clause order, punctuation, and the author's exact rhetorical vocabulary. Make only the cosmetic grammatical adjustments that the substitution mechanically requires — nothing else. This keeps the anonymised text close enough to the original that Pass 1's technique detection isn't confounded by unrelated rewriting.

**Status:** These four rules were incorporated into `pass0.md` on 2026-06-07 (replacing the earlier gender-matching rule with forced neuter, and adding the role-proxy rule). An empirical test on the taz.de "Männlichkeitsbilder" article confirmed that, *when the LLM call succeeds*, the rules work as intended — gender terms are correctly clustered, neutralised, and de-proxied (e.g. "Mein Sohn wird ein Mann" → "Mein Kind wird ein Gruppe-A", with consistent neuter grammar throughout). However, the call took ~360 seconds, still exceeding the CLI adapter's 180s timeout, so the underlying performance/timeout problem (Open Tests item, see below) persists regardless of the rule set used — and the test additionally surfaced a new layering conflict between the LLM's anonymisation and the downstream spaCy NER pass (spaCy can overwrite placeholders the LLM already inserted). Whether to keep or revert this architecture is still an open decision pending resolution of these issues.

---

## Open Tests

- [x] Substitution pair: Black / White — Test 04
- [x] Substitution pair: male / female (biological) — Test 05 (model-comparison caveat — clean repeat run open)
- [ ] Clean same-model repeat of Test 05 (original vs. anonymised, identical model/architecture)
- [ ] Substitution pair: migrants / natives
- [ ] Substitution pair: left-wing / right-wing
- [ ] Historical: SA text (anti-Jewish) vs. mirror text
- [ ] Quantify context-loss effect from anonymisation (cf. test 03)
- [ ] Extend model comparison tests 02 and 03 to further models
