import { Component, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Api } from '../../core/api';
import { Service } from '../../core/models';
import { Heading, ServiceImage } from '../../shared/components';
import { Feedback } from '../../shared/feedback';
import { duration, errorMessage } from '../../shared/presentation';

@Component({
  imports: [CurrencyPipe, RouterLink, Heading, ServiceImage, Feedback],
  templateUrl: './catalog.html',
  styles: '.intro { margin-bottom:15px; }',
})
export class Catalog {
  private readonly api = inject(Api);
  readonly services = signal<Service[]>([]);
  readonly loading = signal(true);
  readonly error = signal('');
  readonly duration = duration;
  constructor() {
    this.load();
  }
  load() {
    this.loading.set(true);
    this.error.set('');
    this.api.services().subscribe({
      next: (services) => {
        this.services.set(services);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.loading.set(false);
      },
    });
  }
}
