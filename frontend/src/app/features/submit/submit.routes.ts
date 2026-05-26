import { Routes } from '@angular/router';

export const SUBMIT_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./submit.component').then(m => m.SubmitComponent),
  },
];
