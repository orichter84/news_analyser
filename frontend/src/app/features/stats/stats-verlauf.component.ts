import { Component, inject, signal, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Chart, ChartConfiguration, registerables } from 'chart.js';
import { ApiService } from '../../core/services/api.service';
import { VerlaufEntry } from '../../core/models/stats.model';
import { StatsResponse } from '../../core/models/stats.model';

Chart.register(...registerables);

@Component({
  selector: 'app-stats-verlauf',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './stats-verlauf.component.html',
})
export class StatsVerlaufComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('orwellCanvas')  orwellCanvas!:  ElementRef<HTMLCanvasElement>;
  @ViewChild('bernaysCanvas') bernaysCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('dkCanvas')      dkCanvas!:      ElementRef<HTMLCanvasElement>;

  private api = inject(ApiService);

  domains    = signal<string[]>([]);
  selectedDomain = signal<string>('');
  data       = signal<VerlaufEntry[]>([]);
  loading    = signal(true);
  hasDk      = signal(false);

  private charts: Chart[] = [];

  ngOnInit() {
    this.api.getStats().subscribe((s: StatsResponse) => {
      this.domains.set(s.domain_averages.map(d => d.domain).sort());
    });
    this.loadData();
  }

  ngAfterViewInit() {
    // Canvases sind in @if-Blöcken — erst nach Daten-Load verfügbar
  }

  ngOnDestroy() {
    this.charts.forEach(c => c.destroy());
  }

  onDomainChange() {
    this.loadData();
  }

  private loadData() {
    this.loading.set(true);
    const domain = this.selectedDomain() || undefined;
    this.api.getVerlauf(domain).subscribe(entries => {
      this.data.set(entries);
      this.hasDk.set(entries.some(e => e.dk_median != null));
      this.loading.set(false);
      setTimeout(() => this.buildCharts(), 0);
    });
  }

  private buildCharts() {
    this.charts.forEach(c => c.destroy());
    this.charts = [];

    const entries = this.data();
    if (!entries.length) return;

    const labels = entries.map(e => e.date);

    if (this.orwellCanvas) {
      this.charts.push(this.makeChart(
        this.orwellCanvas.nativeElement, labels,
        entries.map(e => e.orwell_median),
        'Orwell-Index (Median)', '#a89aff', 0, 1,
      ));
    }
    if (this.bernaysCanvas) {
      this.charts.push(this.makeChart(
        this.bernaysCanvas.nativeElement, labels,
        entries.map(e => e.bernays_median),
        'Bernays Score (Median)', '#52e0a8', 0, undefined,
      ));
    }
    if (this.dkCanvas && this.hasDk()) {
      this.charts.push(this.makeChart(
        this.dkCanvas.nativeElement, labels,
        entries.map(e => e.dk_median ?? null),
        'DK-Index (Median)', '#e07a52', 0, 1,
      ));
    }
  }

  private makeChart(
    canvas: HTMLCanvasElement,
    labels: string[],
    data: (number | null)[],
    label: string,
    color: string,
    yMin: number,
    yMax: number | undefined,
  ): Chart {
    const cfg: ChartConfiguration = {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label,
          data,
          borderColor: color,
          backgroundColor: color + '22',
          pointBackgroundColor: color,
          pointRadius: 4,
          tension: 0.3,
          fill: true,
          spanGaps: true,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            ticks: { color: '#7a7d96', maxTicksLimit: 10 },
            grid:  { color: '#2e3148' },
          },
          y: {
            min: yMin,
            ...(yMax != null ? { max: yMax } : {}),
            ticks: { color: '#7a7d96' },
            grid:  { color: '#2e3148' },
          },
        },
        plugins: {
          legend: { labels: { color: '#e2e4f0' } },
          tooltip: {
            callbacks: {
              afterLabel: (ctx) => {
                const e = this.data()[ctx.dataIndex];
                return `n = ${e.count}`;
              },
            },
          },
        },
      },
    };
    return new Chart(canvas, cfg);
  }
}
