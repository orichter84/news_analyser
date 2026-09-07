import { Routes } from '@angular/router';

export const TECHNIQUES_ROUTES: Routes = [
  {
    path: ':id',
    loadComponent: () => import('./technique-detail.component').then(m => m.TechniqueDetailComponent),
  },
];
