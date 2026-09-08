import { Component } from '@angular/core';

@Component({
  selector: 'app-knowledge-indikatoren',
  standalone: true,
  template: `
<section class="kb-section">
  <h2>4. Die Indikatoren</h2>

  <h3>Warum überhaupt Indikatoren?</h3>
  <p>
    Die Pipeline erzeugt pro Artikel eine Fülle an Detailinformationen — einzelne
    Zitate, erkannte Techniken, die Zielrichtung einzelner Entitäten. Das ist für
    die Detailansicht eines einzelnen Artikels wertvoll, aber nicht
    vergleichbar: Man kann daraus nicht auf einen Blick ablesen, ob Artikel A
    manipulativer ist als Artikel B, oder ob sich ein Herausgeber über Monate
    hinweg verändert hat. Die Indikatoren verdichten diese Details zu wenigen,
    konsistent berechneten Kennzahlen — erst dadurch werden einzelne Artikel,
    Verläufe über Zeit und ganze Herausgeber überhaupt vergleichbar (siehe
    Statistiken → Herausgeber &amp; Trends).
  </p>

  <h3>Woher kommen diese Indikatoren?</h3>
  <div class="kb-callout warning">
    <strong>Keine etablierten Standardmaße</strong>
    Orwell-Index, Bernays Score, Dunning-Kruger-Index und Zitat-Verstärkungs-Index
    sind <strong>keine</strong> wissenschaftlich anerkannten oder journalistisch
    etablierten Kennzahlen — anders als z.&nbsp;B. der Flesch-Lesbarkeitsindex.
    Es sind projekteigene Metriken, die im Rahmen dieses Projekts entwickelt,
    iterativ verfeinert und gegen selbst erstellte Testfälle kalibriert wurden
    (siehe „2. Unser Ansatz" für die Pipeline und „7. Quellen &amp; Inspiration"
    für die Namensgeber). Die konkreten Skalen, Schwellenwerte und die
    Zusammenführung mehrerer Signale (z.&nbsp;B. das Maximum aus struktureller
    und zitatbasierter Bewertung beim Orwell-Index) sind Design-Entscheidungen
    dieses Projekts, kein Ergebnis externer, peer-geprüfter Forschung. Die Namen
    (Orwell, Bernays, Dunning-Kruger) sind bewusst gewählte Anspielungen auf die
    Konzepte, die die jeweilige Kennzahl inspiriert haben — keine Übernahme
    fremder Metriken oder Zitate aus deren Werken. Ein Score sagt daher nichts
    Absolutes aus, sondern ist nur innerhalb dieses Tools und relativ zum
    eigenen Analyse-Korpus zu interpretieren (siehe auch „5. Limitierungen").
  </div>

  <!-- Orwell-Index -->
  <div class="kb-indicator">
    <div class="indicator-header">
      <span class="indicator-score">0.0 – 1.0</span>
      <div>
        <h3>Orwell-Index</h3>
        <span class="indicator-sub">Rhetorischer Extremismus</span>
      </div>
    </div>
    <p>
      Misst die <strong>rhetorische Intensität</strong> eines Textes — richtungsblind.
      Ein linksextremistischer und ein rechtsextremistischer Artikel mit identischer
      rhetorischer Intensität erhalten denselben Score. Die politische Richtung wird
      separat durch die Politische Strömung erfasst.
    </p>
    <p>
      <strong>0.0</strong> steht für sachlich und ausgewogen (Quellenangaben, Konjunktiv,
      keine Feindbilder). <strong>1.0</strong> für totalen Anspruch: existenzielle
      Bedrohungsnarrative, Scapegoating, kein Raum für Differenzierung.
    </p>
    <p>
      Der Wert setzt sich aus zwei unabhängigen Quellen zusammen: der
      <strong>strukturellen</strong> Bewertung der eigenen Autor:innen-Stimme
      (Pass 1, ohne Zitate) und dem <strong>Zitat-Verstärkungs-Index</strong>
      (Pass 2), der misst, wie stark die <em>Auswahl</em> zitierter Aussagen
      extreme Rhetorik verstärkt, ohne Einordnung oder Gegenrede. Es zählt
      jeweils der höhere der beiden Werte — ein Artikel kann also allein durch
      seine Zitatauswahl als extrem gelten, auch wenn die Autor:innen selbst
      sachlich formulieren.
    </p>
    <div class="kb-callout name">
      <strong>Warum „Orwell"?</strong>
      George Orwell (1903–1950) beschrieb in <em>1984</em> und <em>Politics and the
      English Language</em> (1946) präzise, wie Sprache zur Gedankenkontrolle eingesetzt
      wird: <em>Newspeak</em> reduziert den Wortschatz, um bestimmte Gedanken
      undenkbar zu machen. <em>Doppeldenk</em> erlaubt das gleichzeitige Halten
      widersprüchlicher Überzeugungen. Der Index ist nach ihm benannt, weil er
      genau das misst: den Grad, in dem ein Text rhetorisch in Richtung einer
      orwellschen Realitätskontrolle operiert.
    </div>
  </div>

  <!-- Bernays Score -->
  <div class="kb-indicator">
    <div class="indicator-header">
      <span class="indicator-score">Techniken / 1000 Wörter</span>
      <div>
        <h3>Bernays Score</h3>
        <span class="indicator-sub">Manipulationsintensität</span>
      </div>
    </div>
    <p>
      Gibt an, wie <strong>dicht gepackt</strong> die erkannten Manipulationstechniken
      im Text sind — normalisiert auf 1000 Wörter, um Artikel unterschiedlicher
      Länge vergleichbar zu machen. Ein langer Artikel mit wenig Techniken und ein
      kurzer Artikel mit vielen erhalten so einen fairen Vergleichswert.
    </p>
    <p>
      Erkannte Techniken umfassen u.&nbsp;a.: Framing, Loaded Language, Straw
      Man, False Balance, Scapegoating, Appeal to Authority, Emotionale
      Manipulation, Omission, Whataboutism — insgesamt 28 dokumentierte
      Techniken (siehe „6. Manipulationstechniken").
    </p>
    <div class="kb-callout name">
      <strong>Warum „Bernays"?</strong>
      Edward Bernays (1891–1995), Neffe Sigmund Freuds, gilt als Vater der modernen
      Public Relations. In seinem Buch <em>Propaganda</em> (1928) legte er offen dar,
      wie öffentliche Meinung systematisch durch gezielte Rhetorik und emotionale
      Appelle geformt werden kann — Techniken, die heute in politischer Kommunikation
      und Nachrichtenmedien allgegenwärtig sind. Der Score ist nach ihm benannt,
      weil er die Dichte genau dieser Techniken misst.
    </div>
  </div>

  <!-- Dunning-Kruger-Index -->
  <div class="kb-indicator">
    <div class="indicator-header">
      <span class="indicator-score">0.0 – 1.0</span>
      <div>
        <h3>Dunning-Kruger-Index</h3>
        <span class="indicator-sub">Epistemische Überzeugheit</span>
      </div>
    </div>
    <p>
      Ist ein Indikator dafür, wie <strong>überzeugt</strong> ein Text formuliert ist,
      ohne durch Quellen, Konjunktiv oder Einschränkungen gedeckt zu sein.
      Indikatoren: Fehlen von Konjunktiv, Quellenangaben und Einschränkungen;
      häufige absolute Formulierungen.
    </p>
    <p>
      Dieser Index ist bemerkenswert <strong>gruppenblind</strong>: Da epistemische
      Überzeugheit grammatikalisch und strukturell bestimmt wird, liefert er
      konsistente Scores unabhängig davon, über welche Gruppe ein Artikel schreibt —
      empirisch bestätigt in unseren Symmetrie-Tests.
    </p>
    <div class="kb-callout name">
      <strong>Warum „Dunning-Kruger"?</strong>
      David Dunning und Justin Kruger veröffentlichten 1999 die Studie
      <em>Unskilled and Unaware of It</em>, die zeigt: Menschen mit geringem
      Kompetenzlevel in einem Bereich überschätzen ihre Fähigkeiten systematisch,
      weil ihnen das Metawissen fehlt, die eigene Inkompetenz zu erkennen.
      Der Index überträgt dieses Prinzip auf Medientexte: Ein hoher Wert bedeutet,
      dass ein Text eine Gewissheit ausstrahlt, die nicht durch Quellen,
      Einschränkungen oder Konjunktiv gedeckt wird.
    </div>
  </div>

  <!-- Politische Strömung -->
  <div class="kb-indicator">
    <div class="indicator-header">
      <span class="indicator-score">Labels</span>
      <div>
        <h3>Politische Strömung</h3>
        <span class="indicator-sub">Ideologische Verortung</span>
      </div>
    </div>
    <p>
      Statt einer numerischen Links-Rechts-Achse verwenden wir benannte Labels
      (z.&nbsp;B. <em>nationalistisch</em>, <em>sozialistisch</em>,
      <em>konservativ</em>, <em>sozialdemokratisch</em>). Ein Artikel kann
      mehrere Labels erhalten.
    </p>
    <p>
      Diese Entscheidung ist bewusst: Eine eindimensionale Achse scheitert bei
      historisch hybriden Bewegungen. Die NSDAP etwa erhält korrekt
      <em>sozialistisch + nationalistisch + faschistisch</em> — eine Einordnung,
      die auf einer Links-Rechts-Skala strukturell unmöglich wäre und die in
      heutigen Mediendebatten oft ignoriert wird.
    </p>
    <div class="kb-callout name">
      <strong>Warum Labels statt Achse?</strong>
      Das politische Spektrum ist mehrdimensional. Ansätze wie der
      <em>Political Compass</em> (Nolan, 1969) oder Inglehart-Welzel-Werte-Karten
      zeigen: wirtschaftliche und gesellschaftliche Achsen sind orthogonal.
      Labels ermöglichen Überschneidungen und historische Präzision,
      ohne eine falsche Eindimensionalität zu suggerieren.
    </div>
  </div>

  <!-- Themenbereich -->
  <div class="kb-indicator">
    <div class="indicator-header">
      <span class="indicator-score">Kategorie</span>
      <div>
        <h3>Themenbereich</h3>
        <span class="indicator-sub">Thematische Einordnung</span>
      </div>
    </div>
    <p>
      Ordnet jeden Artikel einer thematischen Kategorie zu (z.&nbsp;B.
      <em>Politik</em>, <em>Wirtschaft</em>, <em>Technologie</em>). Wird in
      Pass 2 zusammen mit der politischen Strömung ermittelt und ist u.&nbsp;a.
      Grundlage der Themen-Heatmap in den Statistiken.
    </p>
  </div>

  <!-- Manipulationsziele -->
  <div class="kb-indicator">
    <div class="indicator-header">
      <span class="indicator-score">Entität + Rolle</span>
      <div>
        <h3>Manipulationsziele</h3>
        <span class="indicator-sub">Wer wird wie dargestellt?</span>
      </div>
    </div>
    <p>
      Erfasst für jede im Artikel genannte Entität (Person, Organisation,
      Land …), ob sie <strong>positiv</strong>, <strong>negativ</strong> oder
      <strong>neutral</strong> dargestellt wird, sowie ihre narrative Rolle —
      z.&nbsp;B. <em>Held</em>, <em>Feind</em>, <em>Sündenbock</em>,
      <em>Opfer</em> oder <em>Autorität</em>. Beide Einordnungen werden
      jeweils durch ein wörtliches Zitat aus dem Artikel belegt.
    </p>
    <p>
      Über viele Artikel hinweg aggregiert bilden diese Profile die
      Datengrundlage der Herausgeber-Analyse (Statistiken → Herausgeber),
      die z.&nbsp;B. misst, wie regierungs- oder US-freundlich ein Medium
      über die Zeit berichtet.
    </p>
  </div>
</section>
`,
})
export class KnowledgeIndikatorenComponent {}
