import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    loadChildren: () => import('./features/dashboard/dashboard.routes').then(m => m.DASHBOARD_ROUTES),
  },
  {
    path: 'articles',
    loadChildren: () => import('./features/articles/articles.routes').then(m => m.ARTICLES_ROUTES),
  },
  {
    path: 'stats',
    loadChildren: () => import('./features/stats/stats.routes').then(m => m.STATS_ROUTES),
  },
  {
    path: 'submit',
    loadChildren: () => import('./features/submit/submit.routes').then(m => m.SUBMIT_ROUTES),
  },
  { path: '**', redirectTo: 'dashboard' },
];
