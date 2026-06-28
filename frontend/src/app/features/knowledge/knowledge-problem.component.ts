import { Component } from '@angular/core';

@Component({
  selector: 'app-knowledge-problem',
  standalone: true,
  template: `
<section class="kb-section">
  <h2>1. Das Problem: Medienbias & Modellbias</h2>

  <p>
    Nachrichten sind selten neutral. Jede Redaktion wählt aus, welche Fakten betont,
    welche weggelassen und in welchen emotionalen Rahmen sie eingebettet werden.
    Dieses <em>Framing</em> ist oft subtil — es wirkt, ohne als Manipulation erkannt zu werden.
  </p>

  <h3>LLM-Trainingsbias</h3>
  <p>
    Sprachmodelle lernen aus menschlich erzeugten Texten. Dabei übernehmen sie
    nicht nur Wissen, sondern auch die <strong>asymmetrischen Diskursnormen</strong>
    ihrer Trainingsdaten: Bestimmte gesellschaftliche Gruppen werden in westlichen
    Mediensystemen häufiger als Opfer dargestellt, andere häufiger als Täter —
    unabhängig vom konkreten Sachverhalt.
  </p>
  <p>
    Ein LLM, das auf diesem Korpus trainiert wurde, identifiziert
    <em>Scapegoating</em> oder <em>Loaded Language</em> möglicherweise nicht
    konsistent, wenn dieselbe Rhetorik auf unterschiedliche Zielgruppen angewendet wird.
    Dieser Bias ist keine Frage demografischer Repräsentation, sondern
    <strong>erlernter Diskursnormen</strong> darüber, welche Aussagen als akzeptabel gelten.
  </p>

  <div class="kb-callout warning">
    <strong>Kernproblem:</strong> Ein Analysesystem das selbst auf bias-behafteten Daten
    trainiert wurde, kann Bias nicht zuverlässig messen — es sei denn, es werden
    strukturelle Gegenmaßnahmen ergriffen.
  </div>
</section>
`,
})
export class KnowledgeProblemComponent {}
