import { Component, inject, signal, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Technique } from '../../core/models/technique.model';

@Component({
  selector: 'app-technique-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
<div class="technique-detail-page">
  @if (loading()) {
    <p class="loading">Lade Technik…</p>
  } @else if (error()) {
    <p class="error">{{ error() }}</p>
    <a routerLink="/knowledge/techniken" class="technique-card-more">&larr; Zurück zur Übersicht</a>
  } @else if (technique(); as t) {
    <a routerLink="/knowledge/techniken" class="technique-card-more">&larr; Zurück zur Übersicht</a>

    <div class="technique-detail-header">
      <div class="technique-detail-titles">
        <h1>{{ t.name }}</h1>
        <span class="technique-name-de">{{ t.name_de }}</span>
      </div>
      <span class="tag" [class]="'cat-' + t.category.toLowerCase()">{{ t.category }}</span>
    </div>

    <div class="technique-detail-body">
      <div class="technique-detail-card">
        <h2>Beschreibung</h2>
        <p>{{ t.description }}</p>
      </div>
      @if (t.example) {
        <div class="technique-detail-card">
          <h2>Beispiel</h2>
          <p class="technique-detail-example">{{ t.example }}</p>
        </div>
      }
      @if (t.reference_url) {
        <div class="technique-detail-card source-card">
          <h2>Quelle</h2>
          <a [href]="t.reference_url" target="_blank" rel="noopener" class="wiki-link">Wikipedia &rarr;</a>
        </div>
      }
    </div>
  }
</div>
`,
})
export class TechniqueDetailComponent implements OnInit {
  @Input() id!: string;

  private api = inject(ApiService);
  technique = signal<Technique | null>(null);
  loading = signal(true);
  error = signal('');

  ngOnInit(): void {
    this.api.getTechnique(this.id).subscribe({
      next: t => { this.technique.set(t); this.loading.set(false); },
      error: () => { this.error.set('Technik nicht gefunden.'); this.loading.set(false); },
    });
  }
}
