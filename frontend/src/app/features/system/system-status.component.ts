import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { SystemStatus } from '../../core/models/status.model';

const REFRESH_INTERVAL_MS = 10_000;

const LAST_RUN_LABELS: Record<string, string> = {
  running: 'Wird ausgeführt …',
  ok: 'Erfolgreich',
  no_new_articles: 'Keine neuen Artikel',
  quota_exceeded: 'Gemini-Quota erschöpft',
  quota_cooldown: 'Pausiert (Quota-Sperre)',
  error: 'Fehler',
};

@Component({
  selector: 'app-system-status',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './system-status.component.html',
})
export class SystemStatusComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);
  private timer?: ReturnType<typeof setInterval>;

  status = signal<SystemStatus | null>(null);
  loading = signal(true);
  lastChecked = signal<Date | null>(null);

  ngOnInit() {
    this.refresh();
    this.timer = setInterval(() => this.refresh(), REFRESH_INTERVAL_MS);
  }

  ngOnDestroy() {
    if (this.timer) clearInterval(this.timer);
  }

  refresh() {
    this.api.getSystemStatus().subscribe({
      next: (s) => {
        this.status.set(s);
        this.lastChecked.set(new Date());
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  lastRunLabel(): string {
    const key = this.status()?.feed?.last_run_status;
    if (!key) return '–';
    return LAST_RUN_LABELS[key] ?? key;
  }
}
