import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { expand, map, reduce, EMPTY } from 'rxjs';
import { Booking, BookingInput, Confirmation, Service, ServiceInput, Slot, Status } from './models';

@Injectable({ providedIn: 'root' })
export class Api {
  private readonly http = inject(HttpClient);
  // A API limita páginas a 100. Nunca truncar silenciosamente um catálogo ou agenda.
  private list<T>(path: string, filters: Record<string, string> = {}) {
    const page = (offset: number) =>
      this.http
        .get<T[]>(`/api${path}`, {
          params: new HttpParams({
            fromObject: { ...filters, limite: '100', inicio: String(offset) },
          }),
        })
        .pipe(map((items) => ({ items, offset })));
    return page(0).pipe(
      expand((result) => (result.items.length === 100 ? page(result.offset + 100) : EMPTY)),
      reduce((all, result) => [...all, ...result.items], [] as T[]),
    );
  }
  config() {
    return this.http.get<{ fuso_horario: string }>('/api/publico/configuracao');
  }
  services(admin = false) {
    return this.list<Service>(admin ? '/admin/servicos' : '/publico/servicos');
  }
  service(id: string) {
    return this.http.get<Service>(`/api/publico/servicos/${encodeURIComponent(id)}`);
  }
  availability(id: string) {
    return this.list<Slot>(`/publico/servicos/${encodeURIComponent(id)}/horarios`);
  }
  request(data: BookingInput) {
    return this.http.post<Confirmation>('/api/publico/agendamentos', data);
  }
  saveService(data: ServiceInput, id?: string) {
    return id
      ? this.http.put<Service>(`/api/admin/servicos/${id}`, data)
      : this.http.post<Service>('/api/admin/servicos', data);
  }
  upload(id: string, file: File) {
    return this.http.put<Service>(`/api/admin/servicos/${id}/foto`, file, {
      headers: { 'Content-Type': file.type },
    });
  }
  removePhoto(id: string) {
    return this.http.delete<Service>(`/api/admin/servicos/${id}/foto`);
  }
  slots() {
    return this.list<Slot>('/admin/horarios');
  }
  createSlot(inicio: string, fim: string) {
    return this.http.post<Slot>('/api/admin/horarios', { inicio, fim });
  }
  block(id: string, bloqueado: boolean) {
    return this.http.patch<Slot>(`/api/admin/horarios/${id}/bloqueio`, { bloqueado });
  }
  bookings(status = '') {
    return this.list<Booking>('/admin/agendamentos', status ? { status } : {});
  }
  decide(id: string, status: Exclude<Status, 'pendente'>) {
    return this.http.patch<Booking>(`/api/admin/agendamentos/${id}/status`, { status });
  }
}
