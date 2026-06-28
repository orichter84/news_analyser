import {
  Component, inject, signal, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart, ChartConfiguration, registerables } from 'chart.js';
import { ApiService } from '../../core/services/api.service';
import { TrendResponse, TrendCard, HeatmapRow } from '../../core/models/stats.model';

Chart.register(...registerables);

const CHART_COLORS = [
  '#a89aff', '#52e0a8', '#e07a52', '#52a8e0', '#e0c252',
  '#e052a8', '#52e0e0', '#a8e052', '#e05278',
];

@Component({
  selector: 'app-stats-trends',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './stats-trends.component.html',
})
export class StatsTrendsComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('compCanvas') compCanvas!: ElementRef<HTMLCanvasElement>;

  private api = inject(ApiService);
  private chart: Chart | null = null;

  data    = signal<TrendResponse | null>(null);
  loading = signal(true);

  ngOnInit() {
    this.api.getTrends().subscribe(d => {
      this.data.set(d);
      this.loading.set(false);
      setTimeout(() => this.buildChart(), 0);
    });
  }

  ngAfterViewInit() {}

  ngOnDestroy() {
    this.chart?.destroy();
  }

  private buildChart() {
    const d = this.data();
    if (!d || !this.compCanvas) return;
    this.chart?.destroy();

    const datasets = d.domain_comparison.map((dc, i) => ({
      label: dc.domain,
      data: dc.values,
      borderColor: CHART_COLORS[i % CHART_COLORS.length],
      backgroundColor: 'transparent',
      pointRadius: 3,
      tension: 0.3,
      spanGaps: true,
    }));

    const cfg: ChartConfiguration = {
      type: 'line',
      data: { labels: d.weeks, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#7a7d96' }, grid: { color: '#2e3148' } },
          y: { min: 0, max: 1, ticks: { color: '#7a7d96' }, grid: { color: '#2e3148' } },
        },
        plugins: {
          legend: { labels: { color: '#e2e4f0', boxWidth: 12 } },
          tooltip: { mode: 'index', intersect: false },
        },
      },
    };
    this.chart = new Chart(this.compCanvas.nativeElement, cfg);
  }

  trendClass(pct: number | null): string {
    if (pct === null) return 'trend-neutral';
    if (pct > 5)  return 'trend-up';
    if (pct < -5) return 'trend-down';
    return 'trend-neutral';
  }

  trendArrow(pct: number | null): string {
    if (pct === null) return '–';
    if (pct > 5)  return '↑';
    if (pct < -5) return '↓';
    return '→';
  }

  heatColor(val: number | null): string {
    if (val === null) return 'transparent';
    const r = Math.round(224 * val);
    const g = Math.round(224 * (1 - val) * 0.6);
    return `rgba(${r}, ${g}, 82, ${0.2 + val * 0.7})`;
  }

  cards(): TrendCard[] {
    return this.data()?.trend_cards ?? [];
  }

  heatRows(): HeatmapRow[] {
    return this.data()?.topic_heatmap?.rows ?? [];
  }

  heatWeeks(): string[] {
    return this.data()?.topic_heatmap?.weeks ?? [];
  }

  hasComparison(): boolean {
    return (this.data()?.domain_comparison?.length ?? 0) > 0;
  }
}
