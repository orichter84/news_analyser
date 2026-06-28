import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { Technique } from '../../core/models/technique.model';

@Component({
  selector: 'app-knowledge-techniken',
  standalone: true,
  imports: [CommonModule],
  template: `
<section class="kb-section">
  <h2>6. Manipulationstechniken</h2>
  <p>
    Das System erkennt die folgenden dokumentierten Techniken und normalisiert
    Modell-Ausgaben semantisch auf diese kanonischen Namen.
    Jede Technik ist einer von vier Kategorien zugeordnet:
    <span class="tag cat-emotional">Emotional</span>
    <span class="tag cat-logisch">Logisch</span>
    <span class="tag cat-rhetorisch">Rhetorisch</span>
    <span class="tag cat-strukturell">Strukturell</span>
  </p>

  @for (cat of categories(); track cat) {
    <h3 class="technique-category-heading">
      <span class="tag" [class]="'cat-' + cat.toLowerCase()">{{ cat }}</span>
    </h3>
    <div class="technique-kb-grid">
      @for (t of techniquesByCategory(cat); track t.name) {
        <div class="technique-kb-card">
          <div class="technique-kb-header">
            <strong>{{ t.name }}</strong>
            <span class="technique-name-de">{{ t.name_de }}</span>
          </div>
          <p class="technique-kb-desc">{{ t.description }}</p>
          @if (t.example) {
            <blockquote class="technique-kb-example">{{ t.example }}</blockquote>
          }
          <a [href]="t.reference_url" target="_blank" rel="noopener" class="technique-kb-link">
            Wikipedia &rarr;
          </a>
        </div>
      }
    </div>
  }
</section>
`,
})
export class KnowledgeTechnikenComponent implements OnInit {
  private api = inject(ApiService);

  techniques = signal<Technique[]>([]);
  categories = signal<string[]>([]);

  techniquesByCategory(cat: string): Technique[] {
    return this.techniques().filter(t => t.category === cat);
  }

  ngOnInit(): void {
    this.api.getTechniques().subscribe(list => {
      this.techniques.set(list);
      const cats = [...new Set(list.map(t => t.category))].sort();
      this.categories.set(cats);
    });
  }
}
