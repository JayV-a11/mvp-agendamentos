import { HttpErrorResponse } from '@angular/common/http';
import { AbstractControl, ValidationErrors } from '@angular/forms';

export function errorMessage(error: unknown): string {
  if (!(error instanceof HttpErrorResponse)) return 'Não foi possível concluir. Tente novamente.';
  const messages: Record<number, string> = {
    0: 'Não foi possível conectar. Confira sua conexão e tente novamente.',
    401: 'Sessão expirada ou credenciais inválidas. Entre novamente.',
    403: 'Operação não autorizada. Atualize a página e tente novamente.',
    404: 'Este registro não foi encontrado. Atualize a página.',
    409: 'Os dados foram alterados ou o horário está indisponível. Atualize e tente novamente.',
    413: 'A foto deve ter no máximo 5 MB.',
    415: 'Escolha uma foto JPEG, PNG ou WebP.',
    422: 'Confira os campos informados e o conteúdo da foto, se houver.',
    429: 'Limite de tentativas atingido. Aguarde antes de tentar novamente.',
    503: 'Serviço temporariamente indisponível. Tente novamente mais tarde.',
  };
  return messages[error.status] ?? 'Não foi possível concluir. Tente novamente.';
}

export function duration(minutes: number): string {
  const hours = Math.floor(minutes / 60),
    rest = minutes % 60;
  return hours ? `${hours}h${rest ? ` ${rest}min` : ''}` : `${rest}min`;
}

export function businessDay(instant: string, timezone: string): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date(instant));
  const part = (name: string) => parts.find((p) => p.type === name)!.value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}
export function calendarDate(value: string): string {
  return `${value.slice(8, 10)}/${value.slice(5, 7)}/${value.slice(0, 4)}`;
}

export function phone(control: AbstractControl): ValidationErrors | null {
  const value = String(control.value);
  return /^\+?[0-9 ()-]+$/.test(value) && /^\+?\d{10,15}$/.test(value.replace(/[ ()-]/g, ''))
    ? null
    : { phone: true };
}
export function notBlank(control: AbstractControl): ValidationErrors | null {
  return String(control.value).trim() ? null : { blank: true };
}
export function positivePrice(control: AbstractControl): ValidationErrors | null {
  return Number(String(control.value).replace(',', '.')) > 0 ? null : { positivePrice: true };
}

// Converte datetime-local no fuso do negócio, independentemente do fuso do dispositivo.
export function businessInstant(value: string, timezone: string): string {
  const nominal = Date.parse(`${value}:00Z`);
  if (!Number.isFinite(nominal)) throw new Error('Data inválida');
  let instant = nominal;
  for (let i = 0; i < 3; i++) {
    const parts = new Intl.DateTimeFormat('sv-SE', {
      timeZone: timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    }).format(new Date(instant));
    instant += nominal - Date.parse(`${parts.replace(' ', 'T')}:00Z`);
  }
  const result = new Date(instant).toISOString();
  const local = new Intl.DateTimeFormat('sv-SE', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
    .format(new Date(result))
    .replace(' ', 'T');
  if (local !== value) throw new Error('Horário inválido no fuso do negócio');
  return result;
}
