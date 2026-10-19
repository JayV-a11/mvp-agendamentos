import { Component, effect, input, output, signal } from '@angular/core';

@Component({
  selector: 'app-feedback',
  template: `
    @if ((error() || success()) && !dismissed()) {
      <section
        class="alert feedback-panel"
        [class.error]="!!error()"
        [class.success]="!error()"
        [attr.role]="error() ? 'alert' : 'status'"
        aria-atomic="true"
      >
        <div>
          <strong>{{ error() ? 'Atenção' : '✓ Concluído' }}</strong>
          <p>{{ error() || success() }}</p>
        </div>
        <button
          type="button"
          class="feedback-close"
          (click)="dismissed.set(true); closed.emit()"
          aria-label="Fechar aviso"
        >
          ×
        </button>
      </section>
    }
  `,
})
export class Feedback {
  readonly error = input('');
  readonly success = input('');
  readonly dismissed = signal(false);
  readonly closed = output<void>();

  constructor() {
    effect(() => {
      this.error();
      this.success();
      this.dismissed.set(false);
    });
  }
}
