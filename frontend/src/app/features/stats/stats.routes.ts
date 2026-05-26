import { Routes } from '@angular/router';

export const STATS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./stats.component').then(m => m.StatsComponent),
  },
];
