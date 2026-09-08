import { Component } from '@angular/core';

@Component({
  selector: 'app-knowledge-ansatz',
  standalone: true,
  template: `
<section class="kb-section">
  <h2>2. Unser Ansatz</h2>

  <h3>Pass 0 und Anonymisierung als Strukturlösung</h3>
  <p>
    Statt den LLM-Bias durch Prompt-Engineering zu kompensieren — was ein Katz-und-Maus-Spiel
    ohne Ende wäre — entfernen wir die Ursache: Pass 0 identifiziert vor der
    Extremismus-Analyse explizite menschliche Gruppenbezeichnungen. Anschließend ersetzt
    die Anonymisierung diese zusammen mit Personen und Organisationen durch neutrale
    Platzhalter (<em>Person-A</em>, <em>Org-B</em>, <em>Gruppe-C</em>).
  </p>
  <p>
    Das Modell bewertet damit nur noch die <strong>rhetorische Struktur</strong>
    eines Textes — apokalyptische Sprache, Feindbilder, Mobilisierungsrhetorik —
    unabhängig davon, welche Gruppe gemeint ist.
  </p>

  <h3>Zwei Analyse-Pässe</h3>
  <p>
    Manche Informationen erfordern jedoch den Originaltext — z.&nbsp;B. welche
    politische Strömung ein Artikel vertritt. Nach Pass 0 und der Anonymisierung
    nutzen wir dafür zwei getrennte Analyse-Durchläufe:
  </p>
  <div class="kb-two-pass">
    <div class="pass-card">
      <span class="pass-label">Pass 1</span>
      <strong>Anonymisierter Text</strong>
      <ul>
        <li>Orwell-Index, strukturell (Extremismus der eigenen Stimme)</li>
        <li>Erkannte Manipulationstechniken (Basis für den Bernays Score)</li>
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
        <li>Zitat-Verstärkungs-Index</li>
      </ul>
      <span class="pass-note">Kontextabhängig — mit Prompt-Symmetrie-Instruktion</span>
    </div>
  </div>

  <h3>Zwei Quellen für den Orwell-Index</h3>
  <p>
    Pass 1 blendet Direktzitate bewusst aus — ein Medium soll nicht dafür
    bestraft werden, dass es eine extreme Aussage akkurat zitiert.
    <strong>Welche</strong> Zitate ein Artikel aber prominent platziert, ohne
    Einordnung oder Gegenrede, ist selbst eine redaktionelle Entscheidung.
    Pass 2 bewertet diese Zitatauswahl separat als
    <em>Zitat-Verstärkungs-Index</em>. Der finale Orwell-Index ist das Maximum
    aus beiden Werten — ein Artikel kann also allein durch seine Zitatauswahl
    als extrem gelten, selbst wenn die Autor:innen selbst sachlich und neutral
    formulieren.
  </p>

  <h3>RAG-Kalibrierungsanker</h3>
  <p>
    LLMs neigen dazu, Scores ohne Referenzpunkte inkonsistent zu vergeben.
    Um den Orwell-Index zu stabilisieren, werden nach jeder Analyse ähnliche
    bereits bewertete Artikel aus einer Vektordatenbank abgerufen und als
    dynamische Kalibrierungsbeispiele in den Prompt eingebettet.
    Ähnliche Texte sollten ähnliche Scores erhalten — dieses Prinzip heißt
    <em>Retrieval-Augmented Generation (RAG)</em>. Diese Kalibrierung greift
    erst, sobald mindestens 5 bewertete Artikel als Anker vorliegen — davor
    läuft Pass 1 ohne Referenzbeispiele.
  </p>
</section>
`,
})
export class KnowledgeAnsatzComponent {}
