import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Auth } from '../../core/auth';
import { FieldError, Heading } from '../../shared/components';
import { errorMessage } from '../../shared/presentation';

@Component({
  imports: [ReactiveFormsModule, RouterLink, Heading, FieldError],
  templateUrl: './login.html',
})
export class LoginPage {
  private readonly auth = inject(Auth);
  private readonly router = inject(Router);
  readonly store = this.auth.store;
  readonly busy = signal(false);
  readonly error = signal('');
  readonly form = inject(FormBuilder).nonNullable.group({
    email: ['', [Validators.required, Validators.email, Validators.maxLength(255)]],
    senha: ['', [Validators.required, Validators.maxLength(128)]],
  });
  submit() {
    if (this.busy()) return;
    this.form.markAllAsTouched();
    this.error.set('');
    if (this.form.invalid) return;
    this.busy.set(true);
    const { email, senha } = this.form.getRawValue();
    this.auth.login(email.trim(), senha).subscribe({
      next: () => {
        this.form.controls.senha.reset();
        this.busy.set(false);
        void this.router.navigateByUrl('/admin/agenda');
      },
      error: (error) => {
        this.error.set(errorMessage(error));
        this.form.controls.senha.reset();
        this.busy.set(false);
      },
    });
  }
}
