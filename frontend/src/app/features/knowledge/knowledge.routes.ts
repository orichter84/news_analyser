import { Routes } from '@angular/router';

export const KNOWLEDGE_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./knowledge.component').then(m => m.KnowledgeComponent),
    children: [
      { path: '', redirectTo: 'problem', pathMatch: 'full' },
      {
        path: 'problem',
        loadComponent: () => import('./knowledge-problem.component').then(m => m.KnowledgeProblemComponent),
      },
      {
        path: 'ansatz',
        loadComponent: () => import('./knowledge-ansatz.component').then(m => m.KnowledgeAnsatzComponent),
      },
      {
        path: 'pipeline',
        loadComponent: () => import('./knowledge-pipeline.component').then(m => m.KnowledgePipelineComponent),
      },
      {
        path: 'indikatoren',
        loadComponent: () => import('./knowledge-indikatoren.component').then(m => m.KnowledgeIndikatorenComponent),
      },
      {
        path: 'limitierungen',
        loadComponent: () => import('./knowledge-limitierungen.component').then(m => m.KnowledgeLimitierungenComponent),
      },
      {
        path: 'techniken',
        loadComponent: () => import('./knowledge-techniken.component').then(m => m.KnowledgeTechnikenComponent),
      },
      {
        path: 'quellen',
        loadComponent: () => import('./knowledge-quellen.component').then(m => m.KnowledgeQuellenComponent),
      },
    ],
  },
];
