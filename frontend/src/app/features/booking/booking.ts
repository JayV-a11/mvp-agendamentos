import { Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { Api } from '../../core/api';
import { Confirmation, Service, Slot } from '../../core/models';
import { FieldError, Heading } from '../../shared/components';
import { BusinessDatePipe } from '../../shared/business-date.pipe';
import { Feedback } from '../../shared/feedback';
import {
  businessDay,
  calendarDate,
  duration,
  errorMessage,
  notBlank,
  phone,
} from '../../shared/presentation';

@Component({
  imports: [
    CurrencyPipe,
    BusinessDatePipe,
    RouterLink,
    ReactiveFormsModule,
    Heading,
    FieldError,
    Feedback,
  ],
  templateUrl: './booking.html',
})
export class BookingPage {
  private readonly api = inject(Api);
  private readonly id = inject(ActivatedRoute).snapshot.paramMap.get('id')!;
  readonly service = signal<Service | null>(null);
  readonly slots = signal<Slot[]>([]);
  readonly timezone = signal('America/Sao_Paulo');
  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly confirmation = signal<Confirmation | null>(null);
  readonly day = signal('');
  readonly selected = signal('');
  readonly days = computed(() => [
    ...new Set(this.slots().map((s) => businessDay(s.inicio, this.timezone()))),
  ]);
  readonly visibleSlots = computed(() =>
    this.slots().filter((s) => businessDay(s.inicio, this.timezone()) === this.day()),
  );
  readonly form = inject(FormBuilder).nonNullable.group({
    cliente_nome: ['', [Validators.required, notBlank, Validators.maxLength(150)]],
    cliente_telefone: ['', [Validators.required, phone, Validators.maxLength(30)]],
  });
  readonly duration = duration;
  readonly calendarDate = calendarDate;
  constructor() {
    this.load();
  }
  load() {
    this.loading.set(true);
    this.error.set('');
    this.selected.set('');
    forkJoin({
      service: this.api.service(this.id),
      slots: this.api.availability(this.id),
      config: this.api.config(),
    }).subscribe({
      next: (result) => {
        this.service.set(result.service);
        this.timezone.set(result.config.fuso_horario);
        this.slots.set(result.slots);
        this.day.set(this.days()[0] ?? '');
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.loading.set(false);
      },
    });
  }
  changeDay(day: string) {
    this.day.set(day);
    this.selected.set('');
    this.error.set('');
  }
  submit() {
    if (this.busy() || this.confirmation()) return;
    this.form.markAllAsTouched();
    this.error.set('');
    if (this.form.invalid || !this.selected()) {
      this.error.set('Confira seu nome, telefone e selecione um horário.');
      return;
    }
    this.busy.set(true);
    this.api
      .request({ servico_id: this.id, horario_id: this.selected(), ...this.form.getRawValue() })
      .subscribe({
        next: (confirmation) => {
          this.confirmation.set(confirmation);
          this.form.reset();
          this.selected.set('');
          this.busy.set(false);
        },
        error: (error) => {
          this.error.set(errorMessage(error));
          this.busy.set(false);
          // Após conflito, não permitir reenviar a mesma seleção desatualizada.
          this.selected.set('');
        },
      });
  }
}
