import { HttpErrorResponse } from '@angular/common/http';
import { FormControl } from '@angular/forms';
import { BusinessDatePipe } from './business-date.pipe';
import {
  businessDay,
  businessInstant,
  calendarDate,
  duration,
  errorMessage,
  notBlank,
  phone,
  positivePrice,
} from './presentation';

describe('Apresentação e validações', () => {
  it('formata dia de calendário sem reinterpretar como instante em outro fuso', () =>
    expect(calendarDate('2030-10-30')).toBe('30/10/2030'));
  it('aceita centavos com vírgula e rejeita preço zero ou inválido', () => {
    expect(positivePrice(new FormControl('0,50'))).toBeNull();
    expect(positivePrice(new FormControl('0'))).toEqual({ positivePrice: true });
    expect(positivePrice(new FormControl('abc'))).toEqual({ positivePrice: true });
  });
  it.each([
    [30, '30min'],
    [60, '1h'],
    [90, '1h 30min'],
  ])('formata duração %s', (value, text) => expect(duration(value as number)).toBe(text));
  it.each([0, 401, 403, 404, 409, 413, 415, 422, 429, 503, 500])(
    'traduz erro %s sem refletir corpo sensível',
    (status) => {
      const text = errorMessage(
        new HttpErrorResponse({ status, error: { detail: 'SENHA-SECRETA' } }),
      );
      expect(text.length).toBeGreaterThan(10);
      expect(text).not.toContain('SENHA-SECRETA');
    },
  );
  it('trata falha desconhecida e valores em branco', () => {
    expect(errorMessage(new Error())).toContain('Tente novamente');
    expect(notBlank(new FormControl(' '))).toEqual({ blank: true });
    expect(notBlank(new FormControl('Nome'))).toBeNull();
  });
  it.each(['(11) 99999-0000', '+55 11 99999-0000', '11999990000'])('aceita telefone %s', (value) =>
    expect(phone(new FormControl(value))).toBeNull(),
  );
  it.each(['abc', '123', '+1234567890123456', '11<script>', '++5511999990000'])(
    'rejeita telefone %s',
    (value) => expect(phone(new FormControl(value))).toEqual({ phone: true }),
  );
  it('respeita o dia do negócio quando o instante muda de data em UTC', () => {
    expect(businessDay('2030-10-31T01:00:00Z', 'America/Sao_Paulo')).toBe('2030-10-30');
    const pipe = new BusinessDatePipe();
    expect(pipe.transform('2030-10-31T01:00:00Z', 'America/Sao_Paulo', true)).toBe('22:00');
    expect(pipe.transform('2030-10-31T01:00:00Z', 'America/Sao_Paulo')).toContain('30/10/2030');
  });
  it('converte datetime-local sem usar o fuso do dispositivo', () => {
    expect(businessInstant('2030-10-30T14:00', 'America/Sao_Paulo')).toBe(
      '2030-10-30T17:00:00.000Z',
    );
    expect(() => businessInstant('inválido', 'America/Sao_Paulo')).toThrow();
    expect(() => businessInstant('2030-03-10T02:30', 'America/New_York')).toThrow();
  });
});
