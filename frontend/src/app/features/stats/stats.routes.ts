import { Routes } from '@angular/router';

export const STATS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./stats.component').then(m => m.StatsComponent),
    children: [
      { path: '', redirectTo: 'uebersicht', pathMatch: 'full' },
      {
        path: 'uebersicht',
        loadComponent: () => import('./stats-overview.component').then(m => m.StatsOverviewComponent),
      },
      {
        path: 'verlauf',
        loadComponent: () => import('./stats-verlauf.component').then(m => m.StatsVerlaufComponent),
      },
    ],
  },
];
