import { inject, Injectable, signal } from '@angular/core';
import { HttpInterceptorFn } from '@angular/common/http';
import { NavigationStart, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { defer, finalize } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class Activity {
  readonly pending = signal(0);
  readonly sessionSuccess = signal('');

  constructor() {
    inject(Router)
      .events.pipe(takeUntilDestroyed())
      .subscribe((event) => {
        if (event instanceof NavigationStart) this.sessionSuccess.set('');
      });
  }
}

export const activityInterceptor: HttpInterceptorFn = (request, next) => {
  if (!request.url.startsWith('/api/')) return next(request);
  const activity = inject(Activity);
  return defer(() => {
    activity.pending.update((count) => count + 1);
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method)) activity.sessionSuccess.set('');
    return next(request).pipe(finalize(() => activity.pending.update((count) => count - 1)));
  });
};
