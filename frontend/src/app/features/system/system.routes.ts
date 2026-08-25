import { Routes } from '@angular/router';

export const SYSTEM_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./system-status.component').then(m => m.SystemStatusComponent),
  },
];
