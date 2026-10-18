import { Component, computed, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { Api } from '../../core/api';
import { Booking, Slot, Status } from '../../core/models';
import { Heading, FieldError, StatusBadge } from '../../shared/components';
import { BusinessDatePipe } from '../../shared/business-date.pipe';
import { FocusPanel } from '../../shared/focus-panel';
import { Feedback } from '../../shared/feedback';
import { businessInstant, duration, errorMessage } from '../../shared/presentation';

@Component({
  imports: [
    CurrencyPipe,
    ReactiveFormsModule,
    Heading,
    FieldError,
    StatusBadge,
    BusinessDatePipe,
    FocusPanel,
    Feedback,
  ],
  templateUrl: './agenda.html',
})
export class AgendaPage {
  private readonly api = inject(Api);
  readonly bookings = signal<Booking[]>([]);
  readonly slots = signal<Slot[]>([]);
  readonly timezone = signal('America/Sao_Paulo');
  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly opened = signal(false);
  readonly error = signal('');
  readonly success = signal('');
  readonly filter = signal('');
  readonly visibleBookings = computed(() =>
    this.bookings().filter((b) => !this.filter() || b.status === this.filter()),
  );
  readonly pending = computed(() => this.bookings().filter((b) => b.status === 'pendente').length);
  readonly approved = computed(() => this.bookings().filter((b) => b.status === 'aprovado').length);
  readonly form = inject(FormBuilder).nonNullable.group({
    inicio: ['', Validators.required],
    fim: ['', Validators.required],
  });
  readonly duration = duration;
  constructor() {
    this.load();
  }
  load() {
    this.loading.set(true);
    this.error.set('');
    forkJoin({
      bookings: this.api.bookings(),
      slots: this.api.slots(),
      config: this.api.config(),
    }).subscribe({
      next: (result) => {
        this.bookings.set(result.bookings);
        this.slots.set(result.slots);
        this.timezone.set(result.config.fuso_horario);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.loading.set(false);
      },
    });
  }
  createSlot() {
    if (this.busy()) return;
    this.form.markAllAsTouched();
    this.error.set('');
    this.success.set('');
    if (this.form.invalid) {
      this.error.set('Preencha as datas e os horários de início e fim.');
      return;
    }
    let start: string, end: string;
    try {
      const data = this.form.getRawValue();
      start = businessInstant(data.inicio, this.timezone());
      end = businessInstant(data.fim, this.timezone());
      if (Date.parse(start) <= Date.now() || Date.parse(end) <= Date.parse(start))
        throw new Error('Intervalo inválido');
    } catch {
      this.error.set('Informe início futuro e fim posterior ao início, no fuso informado.');
      return;
    }
    this.busy.set(true);
    this.api.createSlot(start, end).subscribe({
      next: () => {
        this.busy.set(false);
        this.opened.set(false);
        this.form.reset();
        this.success.set('Horário disponibilizado.');
        this.load();
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }
  decide(booking: Booking, status: Exclude<Status, 'pendente'>) {
    if (this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    this.success.set('');
    this.api.decide(booking.id, status).subscribe({
      next: (updated) => {
        this.bookings.update((items) =>
          items.map((item) => (item.id === updated.id ? updated : item)),
        );
        this.busy.set(false);
        this.success.set(`Agendamento ${status} com sucesso.`);
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }
  block(slot: Slot) {
    if (this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    this.success.set('');
    this.api.block(slot.id, !slot.bloqueado).subscribe({
      next: (updated) => {
        this.slots.update((items) =>
          items.map((item) => (item.id === updated.id ? updated : item)),
        );
        this.busy.set(false);
        this.success.set(updated.bloqueado ? 'Horário bloqueado.' : 'Horário desbloqueado.');
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }
  slotState(slot: Slot) {
    if (slot.bloqueado) return 'Bloqueado';
    if (
      this.bookings().some(
        (b) => b.horario_id === slot.id && ['pendente', 'aprovado'].includes(b.status),
      )
    )
      return 'Reservado';
    return Date.parse(slot.inicio) <= Date.now() ? 'Encerrado' : 'Livre';
  }
}
