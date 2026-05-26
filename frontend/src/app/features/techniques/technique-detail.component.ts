import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Technique } from '../../core/models/technique.model';

@Component({
  selector: 'app-technique-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './technique-detail.component.html',
})
export class TechniqueDetailComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  technique = signal<Technique | null>(null);
  error = signal<string | null>(null);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.api.getTechnique(id).subscribe({
      next: t => this.technique.set(t),
      error: () => this.error.set('Technik nicht gefunden.'),
    });
  }
}
