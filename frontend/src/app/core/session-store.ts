import { Injectable, signal } from '@angular/core';
import { AdminSession } from './models';

@Injectable({ providedIn: 'root' })
export class SessionStore {
  readonly session = signal<AdminSession | null>(null);
  readonly expired = signal(false);
  clear(expired = false) {
    this.session.set(null);
    this.expired.set(expired);
  }
}
