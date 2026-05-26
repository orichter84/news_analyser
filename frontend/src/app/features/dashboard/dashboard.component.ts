import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { ArticleListItem } from '../../core/models/article.model';
import { StatsResponse } from '../../core/models/stats.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);

  stats = signal<StatsResponse | null>(null);
  recentArticles = signal<ArticleListItem[]>([]);
  loading = signal(true);

  ngOnInit() {
    this.api.getStats().subscribe(s => {
      this.stats.set(s);
      this.loading.set(false);
    });
    this.api.getArticles({ limit: 10 }).subscribe(a => this.recentArticles.set(a));
  }

  topTechniques(): [string, number][] {
    const t = this.stats()?.top_techniques ?? {};
    return Object.entries(t).slice(0, 5);
  }

  topStroemungen(): [string, number][] {
    const s = this.stats()?.top_stroemungen ?? {};
    return Object.entries(s).slice(0, 6);
  }
}
