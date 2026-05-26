import { Routes } from '@angular/router';

export const TECHNIQUES_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./technique-list.component').then(m => m.TechniqueListComponent),
  },
  {
    path: ':id',
    loadComponent: () =>
      import('./technique-detail.component').then(m => m.TechniqueDetailComponent),
  },
];
