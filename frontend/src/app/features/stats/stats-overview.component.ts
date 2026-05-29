import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { StatsResponse } from '../../core/models/stats.model';

@Component({
  selector: 'app-stats-overview',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './stats-overview.component.html',
})
export class StatsOverviewComponent implements OnInit {
  private api = inject(ApiService);
  stats = signal<StatsResponse | null>(null);
  loading = signal(true);

  ngOnInit() {
    this.api.getStats().subscribe(s => {
      this.stats.set(s);
      this.loading.set(false);
    });
  }

  entries(obj: Record<string, number> | undefined): [string, number][] {
    if (!obj) return [];
    return Object.entries(obj).sort((a, b) => b[1] - a[1]);
  }
}
