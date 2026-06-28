import { Component } from '@angular/core';

@Component({
  selector: 'app-knowledge-ansatz',
  standalone: true,
  template: `
<section class="kb-section">
  <h2>2. Unser Ansatz</h2>

  <h3>Anonymisierung als Strukturlösung</h3>
  <p>
    Statt den LLM-Bias durch Prompt-Engineering zu kompensieren — was ein Katz-und-Maus-Spiel
    ohne Ende wäre — entfernen wir die Ursache: Vor der Extremismus-Analyse werden
    alle Personen- und Organisationsbezeichnungen durch neutrale Platzhalter ersetzt
    (<em>Person-A</em>, <em>Org-B</em>, <em>Gruppe-C</em>).
  </p>
  <p>
    Das Modell bewertet damit nur noch die <strong>rhetorische Struktur</strong>
    eines Textes — apokalyptische Sprache, Feindbilder, Mobilisierungsrhetorik —
    unabhängig davon, welche Gruppe gemeint ist.
  </p>

  <h3>Zwei-Pass-Architektur</h3>
  <p>
    Manche Informationen erfordern jedoch den Originaltext — z.&nbsp;B. welche
    politische Strömung ein Artikel vertritt. Dafür nutzen wir zwei getrennte Analyse-Durchläufe:
  </p>
  <div class="kb-two-pass">
    <div class="pass-card">
      <span class="pass-label">Pass 1</span>
      <strong>Anonymisierter Text</strong>
      <ul>
        <li>Orwell-Index (Extremismus)</li>
        <li>Bernays Score (Techniken)</li>
        <li>Erkannte Manipulationstechniken</li>
      </ul>
      <span class="pass-note">Gruppenblind — strukturell unbiased</span>
    </div>
    <div class="pass-arrow">&rarr;</div>
    <div class="pass-card">
      <span class="pass-label">Pass 2</span>
      <strong>Originaltext</strong>
      <ul>
        <li>Politische Strömung (Labels)</li>
        <li>Dunning-Kruger-Index</li>
        <li>Zielrichtung</li>
      </ul>
      <span class="pass-note">Kontextabhängig — mit Prompt-Symmetrie-Instruktion</span>
    </div>
  </div>

  <h3>RAG-Kalibrierungsanker</h3>
  <p>
    LLMs neigen dazu, Scores ohne Referenzpunkte inkonsistent zu vergeben.
    Um den Orwell-Index zu stabilisieren, werden nach jeder Analyse ähnliche
    bereits bewertete Artikel aus einer Vektordatenbank abgerufen und als
    dynamische Kalibrierungsbeispiele in den Prompt eingebettet.
    Ähnliche Texte sollten ähnliche Scores erhalten — dieses Prinzip heißt
    <em>Retrieval-Augmented Generation (RAG)</em>.
  </p>
</section>
`,
})
export class KnowledgeAnsatzComponent {}
