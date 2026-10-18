import { Routes } from '@angular/router';

import { authGuard } from './core/auth';

export const routes: Routes = [
  {
    path: '',
    title: 'Catálogo | Tranças & Estilo',
    loadComponent: () => import('./features/catalog/catalog').then((m) => m.Catalog),
  },
  {
    path: 'agendar/:id',
    title: 'Solicitar agendamento | Tranças & Estilo',
    loadComponent: () => import('./features/booking/booking').then((m) => m.BookingPage),
  },
  {
    path: 'login',
    title: 'Acesso administrativo | Tranças & Estilo',
    loadComponent: () => import('./features/login/login').then((m) => m.LoginPage),
  },
  {
    path: 'admin',
    canActivate: [authGuard],
    canActivateChild: [authGuard],
    loadComponent: () => import('./features/admin/layout').then((m) => m.AdminLayout),
    children: [
      {
        path: 'agenda',
        title: 'Minha agenda | Tranças & Estilo',
        loadComponent: () => import('./features/admin/agenda').then((m) => m.AgendaPage),
      },
      {
        path: 'servicos',
        title: 'Gerenciar catálogo | Tranças & Estilo',
        loadComponent: () => import('./features/admin/services').then((m) => m.ServicesPage),
      },
      { path: '', pathMatch: 'full', redirectTo: 'agenda' },
    ],
  },
  { path: '**', redirectTo: '' },
];
