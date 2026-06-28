import { Component } from '@angular/core';

@Component({
  selector: 'app-knowledge-quellen',
  standalone: true,
  template: `
<section class="kb-section">
  <h2>7. Quellen & Inspiration</h2>

  <div class="kb-source-grid">
    <div class="kb-source-card">
      <span class="source-year">1928</span>
      <div>
        <strong>
          <a href="https://de.wikipedia.org/wiki/Edward_Bernays" target="_blank" rel="noopener">Edward Bernays</a>
          — <a href="https://de.wikipedia.org/wiki/Propaganda_(Bernays)" target="_blank" rel="noopener"><em>Propaganda</em></a>
        </strong>
        <p>Grundlagenwerk der modernen PR. Bernays beschreibt, wie öffentliche
        Meinung durch gezielte Rhetorik und emotionale Appelle geformt wird —
        Namensgeber des Bernays Score.</p>
      </div>
    </div>
    <div class="kb-source-card">
      <span class="source-year">1946</span>
      <div>
        <strong>
          <a href="https://de.wikipedia.org/wiki/George_Orwell" target="_blank" rel="noopener">George Orwell</a>
          — <a href="https://en.wikipedia.org/wiki/Politics_and_the_English_Language" target="_blank" rel="noopener"><em>Politics and the English Language</em></a>
        </strong>
        <p>Essayistisches Manifest gegen politische Sprachverderbnis.
        Orwell analysiert, wie vage, übertriebene und korrumpierte Sprache
        klares Denken verhindert — Namensgeber des Orwell-Index.</p>
      </div>
    </div>
    <div class="kb-source-card">
      <span class="source-year">1949</span>
      <div>
        <strong>
          <a href="https://de.wikipedia.org/wiki/George_Orwell" target="_blank" rel="noopener">George Orwell</a>
          — <a href="https://de.wikipedia.org/wiki/1984_(Roman)" target="_blank" rel="noopener"><em>Nineteen Eighty-Four</em></a>
        </strong>
        <p>Roman über totale Gedankenkontrolle durch Sprache (Newspeak, Doppeldenk).
        Definiert den konzeptionellen Rahmen für den Orwell-Index als
        Extremismus-Messung.</p>
      </div>
    </div>
    <div class="kb-source-card">
      <span class="source-year">1969</span>
      <div>
        <strong>
          <a href="https://de.wikipedia.org/wiki/David_Nolan_(Politiker)" target="_blank" rel="noopener">David Nolan</a>
          — <a href="https://de.wikipedia.org/wiki/Politisches_Spektrum" target="_blank" rel="noopener"><em>Political Compass</em></a>
        </strong>
        <p>Erste systematische Darstellung des politischen Spektrums als
        zweidimensionale Karte (wirtschaftlich × gesellschaftlich).
        Konzeptuelle Grundlage für unsere Label-statt-Achse-Entscheidung.</p>
      </div>
    </div>
    <div class="kb-source-card">
      <span class="source-year">1999</span>
      <div>
        <strong>
          <a href="https://de.wikipedia.org/wiki/Dunning-Kruger-Effekt" target="_blank" rel="noopener">Dunning &amp; Kruger</a>
          — <em>Unskilled and Unaware of It</em>
        </strong>
        <p>Studie über die systematische Überschätzung eigener Kompetenz.
        Journal of Personality and Social Psychology, 77(6), 1121–1134.
        Namensgeber des Dunning-Kruger-Index.</p>
      </div>
    </div>
    <div class="kb-source-card">
      <span class="source-year">2008</span>
      <div>
        <strong>
          <a href="https://de.wikipedia.org/wiki/Ronald_Inglehart" target="_blank" rel="noopener">Inglehart</a>
          &amp;
          <a href="https://de.wikipedia.org/wiki/Christian_Welzel" target="_blank" rel="noopener">Welzel</a>
          — <em>Changing Mass Priorities</em>
        </strong>
        <p>Weltweite Wertekarten zeigen die Mehrdimensionalität politischer
        Überzeugungen — Unterstützung für unser mehrdimensionales Label-Modell.</p>
      </div>
    </div>
  </div>
</section>
`,
})
export class KnowledgeQuellenComponent {}
