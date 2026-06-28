import { Component } from '@angular/core';

@Component({
  selector: 'app-knowledge-limitierungen',
  standalone: true,
  template: `
<section class="kb-section">
  <h2>5. Limitierungen</h2>

  <div class="kb-limit-grid">
    <div class="kb-limit-card">
      <h4>Kein Faktencheck</h4>
      <p>Das System bewertet rhetorische Strukturen, nicht die inhaltliche Wahrheit
      einer Aussage. Ein sachlich falscher Artikel kann einen niedrigen Orwell-Index
      haben, wenn er nüchtern formuliert ist.</p>
    </div>
    <div class="kb-limit-card">
      <h4>LLM-Outputs sind Schätzungen</h4>
      <p>Alle Scores sind Modellschätzungen, keine objektiven Messungen.
      Kalibrierungsanker und Anonymisierung reduzieren Inkonsistenz,
      eliminieren sie aber nicht vollständig.</p>
    </div>
    <div class="kb-limit-card">
      <h4>Residualer Modellbias in Pass 2</h4>
      <p>Die Anonymisierung schützt Pass 1. In Pass 2 (Politische Strömung)
      kann LLM-Trainingsbias noch wirken. Symmetrie-Tests dokumentieren dies
      und werden kontinuierlich erweitert.</p>
    </div>
    <div class="kb-limit-card">
      <h4>Kein Echtzeitvergleich</h4>
      <p>Scores sind relativ zum analysierten Korpus, nicht absolut.
      Ein 0.6er-Artikel heute kann sich anders anfühlen, wenn der Korpus
      hauptsächlich aus 0.9er-Artikeln besteht.</p>
    </div>
    <div class="kb-limit-card">
      <h4>Sprache: Deutsch</h4>
      <p>Anonymisierung und Keyword-Listen sind auf deutschsprachige
      Texte optimiert. Englische Artikel können analysiert werden,
      liefern aber weniger zuverlässige Ergebnisse.</p>
    </div>
    <div class="kb-limit-card">
      <h4>Paywall-Artikel</h4>
      <p>Artikel hinter Paywalls liefern oft nur Teaser-Text.
      Analysen auf Basis von &lt; 500 Zeichen sind wenig aussagekräftig.</p>
    </div>
  </div>
</section>
`,
})
export class KnowledgeLimitierungenComponent {}
