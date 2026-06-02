import { Component, inject, signal, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { ArticleDetail } from '../../core/models/article.model';
import type { PolitischeStroemung } from '../../core/models/article.model';

@Component({
  selector: 'app-article-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './article-detail.component.html',
})
export class ArticleDetailComponent implements OnInit {
  @Input() url!: string;

  private api = inject(ApiService);
  article = signal<ArticleDetail | null>(null);
  loading = signal(true);
  error = signal('');

  toTechniqueId(name: string): string {
    return name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  }

  isStroemungObject(s: string | PolitischeStroemung): s is PolitischeStroemung {
    return typeof s === 'object' && s !== null;
  }

  ngOnInit() {
    const decodedUrl = decodeURIComponent(this.url);
    this.api.getArticle(decodedUrl).subscribe({
      next: a => { this.article.set(a); this.loading.set(false); },
      error: () => { this.error.set('Artikel nicht gefunden.'); this.loading.set(false); },
    });
  }
}
