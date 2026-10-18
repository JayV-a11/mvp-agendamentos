import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'businessDate' })
export class BusinessDatePipe implements PipeTransform {
  transform(value: string, timezone: string, timeOnly = false): string {
    const options: Intl.DateTimeFormatOptions = timeOnly
      ? { timeZone: timezone, hour: '2-digit', minute: '2-digit' }
      : {
          timeZone: timezone,
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        };
    return new Intl.DateTimeFormat('pt-BR', options).format(new Date(value));
  }
}
