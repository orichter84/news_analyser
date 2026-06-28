import { Component } from '@angular/core';

@Component({
  selector: 'app-knowledge-pipeline',
  standalone: true,
  template: `
<section class="kb-section">
  <h2>3. Die Pipeline</h2>

  <div class="kb-pipeline">
    <div class="pipe-step">
      <span class="pipe-num">1</span>
      <div>
        <strong>Scraping</strong>
        <p>trafilatura extrahiert Text, Titel, Autor und Datum. BeautifulSoup als Fallback.</p>
      </div>
    </div>
    <div class="pipe-step">
      <span class="pipe-num">2</span>
      <div>
        <strong>Keyword-Signal</strong>
        <p>Vorgefilterte Extremismus-Vokabular-Listen liefern einen schwachen Vorab-Score (20–30&nbsp;% Gewicht).</p>
      </div>
    </div>
    <div class="pipe-step">
      <span class="pipe-num">3</span>
      <div>
        <strong>Anonymisierung</strong>
        <p>spaCy (de_core_news_md) ersetzt Personen und Organisationen durch Platzhalter.</p>
      </div>
    </div>
    <div class="pipe-step">
      <span class="pipe-num">4</span>
      <div>
        <strong>RAG-Anker-Abruf</strong>
        <p>Die 3 ähnlichsten bereits bewerteten Artikel werden aus ChromaDB abgerufen.</p>
      </div>
    </div>
    <div class="pipe-step">
      <span class="pipe-num">5</span>
      <div>
        <strong>Pass 1 — LLM (anonymisiert)</strong>
        <p>Orwell-Index, Bernays Score, Manipulationstechniken mit Zitaten.</p>
      </div>
    </div>
    <div class="pipe-step">
      <span class="pipe-num">6</span>
      <div>
        <strong>Pass 2 — LLM (Original)</strong>
        <p>Politische Strömung als Labels, Dunning-Kruger-Index.</p>
      </div>
    </div>
    <div class="pipe-step">
      <span class="pipe-num">7</span>
      <div>
        <strong>Speicherung</strong>
        <p>Ergebnis und Einbettung in ChromaDB. Artikel wird automatisch als neuer Kalibrierungsanker gespeichert.</p>
      </div>
    </div>
  </div>
</section>
`,
})
export class KnowledgePipelineComponent {}
