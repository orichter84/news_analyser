import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { JobStatus } from '../../core/models/analyse.model';

@Component({
  selector: 'app-submit',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './submit.component.html',
})
export class SubmitComponent {
  private api = inject(ApiService);

  url = '';
  force = false;
  submitting = signal(false);
  jobId = signal<string | null>(null);
  jobStatus = signal<JobStatus | null>(null);
  message = signal('');
  pollInterval: ReturnType<typeof setInterval> | null = null;

  submit() {
    if (!this.url) return;
    this.submitting.set(true);
    this.message.set('');
    this.jobId.set(null);
    this.jobStatus.set(null);

    this.api.submitAnalyse({ url: this.url, force: this.force }).subscribe({
      next: res => {
        this.submitting.set(false);
        this.message.set(res.message);
        if (res.job_id) {
          this.jobId.set(res.job_id);
          this.pollStatus(res.job_id);
        }
      },
      error: () => {
        this.submitting.set(false);
        this.message.set('Fehler beim Einreichen der URL.');
      },
    });
  }

  private pollStatus(id: string) {
    this.pollInterval = setInterval(() => {
      this.api.getJobStatus(id).subscribe(s => {
        this.jobStatus.set(s);
        if (s.status === 'done' || s.status === 'error') {
          clearInterval(this.pollInterval!);
        }
      });
    }, 2000);
  }
}
