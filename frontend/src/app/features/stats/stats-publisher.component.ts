import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { PublisherProfile, DependencyScore } from '../../core/models/stats.model';

@Component({
  selector: 'app-stats-publisher',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './stats-publisher.component.html',
})
export class StatsPublisherComponent implements OnInit {
  private api = inject(ApiService);

  profiles = signal<PublisherProfile[]>([]);
  loading = signal(true);
  selected = signal<PublisherProfile | null>(null);

  readonly DEPENDENCY_KEYS = ['regierung', 'usa', 'eu', 'russland', 'china'];
  readonly Math = Math;

  ngOnInit() {
    this.api.getPublisherProfiles().subscribe(p => {
      this.profiles.set(p);
      if (p.length > 0) this.selected.set(p[0]);
      this.loading.set(false);
    });
  }

  select(p: PublisherProfile) {
    this.selected.set(p);
  }

  stroemungEntries(p: PublisherProfile): [string, number][] {
    return Object.entries(p.stroemung).sort((a, b) => b[1] - a[1]).slice(0, 6);
  }

  maxStroemung(p: PublisherProfile): number {
    const vals = Object.values(p.stroemung);
    return vals.length ? Math.max(...vals) : 1;
  }

  dep(p: PublisherProfile, key: string): DependencyScore | null {
    return p.abhaengigkeit[key] ?? null;
  }

  scorePercent(score: number | null): number {
    if (score === null) return 50;
    return Math.round((score + 1) / 2 * 100);
  }

  scoreLabel(score: number | null): string {
    if (score === null) return '–';
    if (score > 0.4) return 'freundlich';
    if (score > 0.1) return 'eher freundlich';
    if (score >= -0.1) return 'neutral';
    if (score >= -0.4) return 'eher kritisch';
    return 'kritisch';
  }

  scoreClass(score: number | null): string {
    if (score === null) return 'no-data';
    if (score > 0.2) return 'positive';
    if (score < -0.2) return 'negative';
    return 'neutral';
  }
}
