import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Technique } from '../../core/models/technique.model';

@Component({
  selector: 'app-technique-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './technique-list.component.html',
})
export class TechniqueListComponent implements OnInit {
  private api = inject(ApiService);

  techniques = signal<Technique[]>([]);
  categories = signal<string[]>([]);

  techniquesByCategory(cat: string): Technique[] {
    return this.techniques().filter(t => t.category === cat);
  }

  ngOnInit(): void {
    this.api.getTechniques().subscribe(list => {
      this.techniques.set(list);
      const cats = [...new Set(list.map(t => t.category))].sort();
      this.categories.set(cats);
    });
  }
}
