import { Component, computed, effect, input, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { map, startWith, switchMap } from 'rxjs';
import { AbstractControl } from '@angular/forms';
import { Service, Status } from '../core/models';

@Component({
  selector: 'app-heading',
  template: ` <header class="brand">
    <span class="brand-mark" aria-hidden="true">T</span>
    <div>
      <p class="brand-name">Tranças &amp; Estilo</p>
      <p class="brand-subtitle">{{ subtitle() }}</p>
    </div>
  </header>`,
})
export class Heading {
  readonly subtitle = input.required<string>();
}

@Component({
  selector: 'app-field-error',
  template: `
    @if (invalid()) {
      <p class="field-error">{{ message() }}</p>
    }
  `,
})
export class FieldError {
  readonly control = input.required<AbstractControl>();
  readonly message = input.required<string>();
  readonly invalid = toSignal(
    toObservable(this.control).pipe(
      switchMap((control) =>
        control.events.pipe(
          startWith(null),
          map(() => control.invalid && control.touched),
        ),
      ),
    ),
    { initialValue: false },
  );
}

@Component({
  selector: 'app-status',
  template: `<span class="badge" [class]="'badge status-' + status()">{{
    labels[status()]
  }}</span>`,
})
export class StatusBadge {
  readonly status = input.required<Status>();
  readonly labels = {
    pendente: 'Pendente',
    aprovado: 'Aprovado',
    recusado: 'Recusado',
    cancelado: 'Cancelado',
  };
}

@Component({
  selector: 'app-service-image',
  host: { class: 'service-image' },
  template: `
    @if (service().imagem_url && !failed()) {
      <img
        [src]="source()"
        [alt]="'Fotografia de ' + service().nome"
        width="104"
        height="112"
        loading="lazy"
        (error)="failed.set(true)"
      />
    } @else {
      <span role="img" [attr.aria-label]="service().nome + ': sem fotografia cadastrada'">{{
        initial()
      }}</span>
    }
  `,
})
export class ServiceImage {
  readonly service = input.required<Service>();
  readonly admin = input(false);
  readonly failed = signal(false);
  readonly initial = computed(() =>
    this.service()
      .nome.replace(/^Tranças?\s+/i, '')
      .slice(0, 1)
      .toLocaleUpperCase('pt-BR'),
  );
  constructor() {
    effect(() => {
      this.service();
      this.failed.set(false);
    });
  }
  source() {
    const service = this.service();
    const query = service.imagem_url!.split('?')[1] ?? '';
    return `/api/${this.admin() ? 'admin' : 'publico'}/servicos/${encodeURIComponent(service.id)}/foto?${query}`;
  }
}
