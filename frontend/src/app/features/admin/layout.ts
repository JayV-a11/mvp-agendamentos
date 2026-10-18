import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { Auth } from '../../core/auth';
import { errorMessage } from '../../shared/presentation';
import { Feedback } from '../../shared/feedback';
import { Activity } from '../../core/activity';

@Component({
  imports: [RouterLink, RouterLinkActive, RouterOutlet, Feedback],
  template: `
    <router-outlet />
    <nav class="admin-nav" aria-label="Administração">
      <a routerLink="/admin/agenda" routerLinkActive="current" ariaCurrentWhenActive="page"
        >Agenda</a
      >
      <a routerLink="/admin/servicos" routerLinkActive="current" ariaCurrentWhenActive="page"
        >Catálogo</a
      >
      <button type="button" (click)="logout()" [disabled]="busy()">
        {{ busy() ? 'Saindo…' : 'Sair' }}
      </button>
    </nav>
    <app-feedback [error]="error()" (closed)="error.set('')" />
    <a class="footer-link" routerLink="/">Ver catálogo público →</a>
  `,
})
export class AdminLayout {
  private readonly auth = inject(Auth);
  private readonly router = inject(Router);
  private readonly activity = inject(Activity);
  readonly busy = signal(false);
  readonly error = signal('');
  logout() {
    if (this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    this.auth.logout().subscribe({
      next: () => {
        this.busy.set(false);
        void this.router.navigateByUrl('/login').then(() => {
          this.activity.sessionSuccess.set('Você saiu da sua conta com segurança.');
        });
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.busy.set(false);
      },
    });
  }
}
