import { Component, inject, signal, ElementRef, ViewChild, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { SystemStatus, LogName } from '../../core/models/status.model';

const REFRESH_INTERVAL_MS = 10_000;

const LAST_RUN_LABELS: Record<string, string> = {
  running: 'Wird ausgeführt …',
  ok: 'Erfolgreich',
  no_new_articles: 'Keine neuen Artikel',
  quota_exceeded: 'Gemini-Quota erschöpft',
  quota_cooldown: 'Pausiert (Quota-Sperre)',
  error: 'Fehler',
};

const LOG_TABS: { name: LogName; label: string }[] = [
  { name: 'app', label: 'App-Log' },
  { name: 'chroma', label: 'ChromaDB' },
  { name: 'backend', label: 'Backend' },
  { name: 'frontend', label: 'Frontend' },
];

@Component({
  selector: 'app-system-status',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './system-status.component.html',
})
export class SystemStatusComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);
  private timer?: ReturnType<typeof setInterval>;

  @ViewChild('logBox') private logBox?: ElementRef<HTMLElement>;

  status = signal<SystemStatus | null>(null);
  loading = signal(true);
  lastChecked = signal<Date | null>(null);

  logTabs = LOG_TABS;
  activeLog = signal<LogName>('app');
  logLines = signal<string[]>([]);
  logLoading = signal(true);

  ngOnInit() {
    this.refresh();
    this.refreshLog();
    this.timer = setInterval(() => {
      this.refresh();
      this.refreshLog();
    }, REFRESH_INTERVAL_MS);
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

  selectLog(name: LogName) {
    if (name === this.activeLog()) return;
    this.activeLog.set(name);
    this.logLoading.set(true);
    this.refreshLog();
  }

  refreshLog() {
    this.api.getLog(this.activeLog()).subscribe({
      next: (res) => {
        this.logLines.set(res.lines);
        this.logLoading.set(false);
        this.scrollLogToBottom();
      },
      error: () => this.logLoading.set(false),
    });
  }

  private scrollLogToBottom() {
    setTimeout(() => {
      const el = this.logBox?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }

  lastRunLabel(): string {
    const key = this.status()?.feed?.last_run_status;
    if (!key) return '–';
    return LAST_RUN_LABELS[key] ?? key;
  }
}
