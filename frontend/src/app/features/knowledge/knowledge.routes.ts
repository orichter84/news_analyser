import { Routes } from '@angular/router';

export const KNOWLEDGE_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./knowledge.component').then(m => m.KnowledgeComponent),
  },
];
