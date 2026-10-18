import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { LoginPage } from './login';
import { SESSION } from '../../../testing/fixtures';

describe('Login administrativo', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  it('mostra campos com rótulo persistente e senha protegida', () => {
    const fixture = TestBed.createComponent(LoginPage);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('label[for=email]')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('#password').type).toBe('password');
    fixture.componentInstance.submit();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Informe um e-mail válido');
    http.expectNone('/api/auth/login');
  });
  it('autentica, evita duplicação e navega para a agenda limpando senha', () => {
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const fixture = TestBed.createComponent(LoginPage),
      page = fixture.componentInstance;
    page.form.setValue({ email: 'admin@example.test', senha: 'Senha sintética' });
    page.submit();
    page.submit();
    http.expectOne('/api/auth/login').flush(SESSION);
    expect(page.form.controls.senha.value).toBe('');
    expect(navigate).toHaveBeenCalledWith('/admin/agenda');
    expect(page.busy()).toBe(false);
  });
  it('mostra erro genérico, limpa senha e permite nova tentativa', () => {
    const fixture = TestBed.createComponent(LoginPage),
      page = fixture.componentInstance;
    page.form.setValue({ email: 'admin@example.test', senha: 'Senha errada' });
    page.submit();
    http
      .expectOne('/api/auth/login')
      .flush({ detail: 'Não refletir' }, { status: 401, statusText: 'Unauthorized' });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=alert]')).not.toBeNull();
    expect(page.form.controls.senha.value).toBe('');
    expect(page.busy()).toBe(false);
    page.store.expired.set(true);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Sua sessão expirou');
  });
});
