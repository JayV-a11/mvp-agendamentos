import { Component, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { of, switchMap } from 'rxjs';
import { Api } from '../../core/api';
import { Service, ServiceInput } from '../../core/models';
import { FieldError, Heading, ServiceImage } from '../../shared/components';
import { FocusPanel } from '../../shared/focus-panel';
import { duration, errorMessage, notBlank, positivePrice } from '../../shared/presentation';

@Component({
  imports: [CurrencyPipe, ReactiveFormsModule, Heading, ServiceImage, FieldError, FocusPanel],
  templateUrl: './services.html',
})
export class ServicesPage {
  private readonly api = inject(Api);
  readonly services = signal<Service[]>([]);
  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly success = signal('');
  readonly opened = signal(false);
  readonly editing = signal<Service | null>(null);
  readonly file = signal<File | null>(null);
  readonly fileError = signal('');
  readonly duration = duration;
  readonly form = inject(FormBuilder).nonNullable.group({
    nome: ['', [Validators.required, notBlank, Validators.maxLength(150)]],
    descricao: ['', Validators.maxLength(5000)],
    preco: [
      '',
      [Validators.required, Validators.pattern(/^\d{1,8}([.,]\d{1,2})?$/), positivePrice],
    ],
    duracao_minutos: [
      60,
      [
        Validators.required,
        Validators.min(1),
        Validators.max(2147483647),
        Validators.pattern(/^\d+$/),
      ],
    ],
    ativo: [true],
  });
  constructor() {
    this.load();
  }
  load() {
    this.loading.set(true);
    this.error.set('');
    this.api.services(true).subscribe({
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
  edit(service: Service | null) {
    if (this.busy() || this.loading()) return;
    this.editing.set(service);
    this.file.set(null);
    this.fileError.set('');
    this.success.set('');
    this.error.set('');
    this.form.reset(
      service
        ? {
            nome: service.nome,
            descricao: service.descricao ?? '',
            preco: service.preco,
            duracao_minutos: service.duracao_minutos,
            ativo: service.ativo,
          }
        : { nome: '', descricao: '', preco: '', duracao_minutos: 60, ativo: true },
    );
    this.opened.set(true);
  }
  selectFile(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.file.set(null);
    this.fileError.set('');
    if (!file) return;
    if (
      !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) ||
      file.size > 5 * 1024 * 1024
    ) {
      this.fileError.set('Escolha uma foto JPEG, PNG ou WebP de até 5 MB.');
      input.value = '';
      return;
    }
    this.file.set(file);
  }
  save() {
    if (this.busy() || this.loading()) return;
    this.form.markAllAsTouched();
    if (this.form.invalid || this.fileError()) return;
    this.busy.set(true);
    this.error.set('');
    this.success.set('');
    const raw = this.form.getRawValue();
    const data: ServiceInput = {
      ...raw,
      descricao: raw.descricao.trim() || null,
      preco: raw.preco.replace(',', '.'),
    };
    let savedBeforePhoto = false;
    this.api
      .saveService(data, this.editing()?.id)
      .pipe(
        switchMap((saved) => {
          savedBeforePhoto = true;
          this.editing.set(saved);
          const file = this.file();
          return file ? this.api.upload(saved.id, file) : of(saved);
        }),
      )
      .subscribe({
        next: () => {
          this.busy.set(false);
          this.opened.set(false);
          this.file.set(null);
          this.success.set('Serviço salvo com sucesso.');
          this.load();
        },
        error: (error) => {
          this.busy.set(false);
          this.error.set(
            (savedBeforePhoto
              ? 'O serviço foi salvo, mas a foto não foi enviada. Você pode tentar salvar novamente. '
              : '') + errorMessage(error),
          );
        },
      });
  }
  toggle(service: Service) {
    if (this.busy() || this.loading()) return;
    this.busy.set(true);
    this.error.set('');
    this.success.set('');
    const { nome, descricao, preco, duracao_minutos, ativo } = service;
    this.api
      .saveService({ nome, descricao, preco, duracao_minutos, ativo: !ativo }, service.id)
      .subscribe({
        next: (updated) => {
          this.services.update((items) =>
            items.map((item) => (item.id === updated.id ? updated : item)),
          );
          this.busy.set(false);
          this.success.set(ativo ? 'Serviço desativado.' : 'Serviço reativado.');
          this.load();
        },
        error: (error) => {
          this.busy.set(false);
          this.error.set(errorMessage(error));
        },
      });
  }
  removePhoto() {
    const service = this.editing();
    if (!service || this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    this.api.removePhoto(service.id).subscribe({
      next: (saved) => {
        this.editing.set(saved);
        this.busy.set(false);
        this.success.set('Foto removida.');
        this.load();
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(errorMessage(error));
      },
    });
  }
}
