import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of, tap, throwError } from 'rxjs';
import { AdminSession } from './models';
import { SessionStore } from './session-store';

@Injectable({ providedIn: 'root' })
export class Auth {
  private readonly http = inject(HttpClient);
  readonly store = inject(SessionStore);
  login(email: string, senha: string) {
    return this.http.post<AdminSession>('/api/auth/login', { email, senha }).pipe(
      tap((s) => {
        this.store.session.set(s);
        this.store.expired.set(false);
      }),
    );
  }
  restore() {
    const current = this.store.session();
    if (current && Date.parse(current.expira_em) > Date.now()) return of(current);
    return this.http
      .get<AdminSession>('/api/auth/sessao')
      .pipe(tap((s) => this.store.session.set(s)));
  }
  logout() {
    return this.http.post<void>('/api/auth/logout', {}).pipe(tap(() => this.store.clear()));
  }
}

export const authGuard: CanActivateFn = () => {
  const auth = inject(Auth);
  const router = inject(Router);
  return auth.restore().pipe(
    map(() => true),
    catchError(() => of(router.createUrlTree(['/login']))),
  );
};

export const sessionInterceptor: HttpInterceptorFn = (request, next) => {
  if (!request.url.startsWith('/api/')) return next(request);
  const store = inject(SessionStore);
  const router = inject(Router);
  const session = store.session();
  let outgoing = request.clone({ withCredentials: true });
  if (session && !['GET', 'HEAD', 'OPTIONS'].includes(request.method)) {
    outgoing = outgoing.clone({ setHeaders: { 'X-CSRF-Token': session.csrf_token } });
  }
  return next(outgoing).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && request.url !== '/api/auth/login') {
        store.clear(store.session() !== null || request.url !== '/api/auth/sessao');
        if (request.url.startsWith('/api/admin/') || request.url === '/api/auth/logout') {
          void router.navigateByUrl('/login');
        }
      }
      return throwError(() => error);
    }),
  );
};
