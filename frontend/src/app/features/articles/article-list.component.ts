import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { ArticleListItem, ArticleFilter } from '../../core/models/article.model';

@Component({
  selector: 'app-article-list',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './article-list.component.html',
})
export class ArticleListComponent implements OnInit {
  private api = inject(ApiService);

  articles = signal<ArticleListItem[]>([]);
  loading = signal(true);

  filter: ArticleFilter = { orwell_min: 0, orwell_max: 1, limit: 50 };

  ngOnInit() {
    this.load();
  }

  load() {
    this.loading.set(true);
    this.api.getArticles(this.filter).subscribe(a => {
      this.articles.set(a);
      this.loading.set(false);
    });
  }
}
