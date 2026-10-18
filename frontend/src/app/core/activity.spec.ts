import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { App } from '../app';
import { Activity, activityInterceptor } from './activity';

describe('Retorno visual das requisições', () => {
  let http: HttpTestingController, client: HttpClient, activity: Activity;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([activityInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpTestingController);
    client = TestBed.inject(HttpClient);
    activity = TestBed.inject(Activity);
  });
  afterEach(() => http.verify());

  it('mantém o progresso visível até concluir todas as requisições, inclusive em erro', () => {
    const fixture = TestBed.createComponent(App);
    client.get('/api/primeira').subscribe();
    client.get('/api/segunda').subscribe({ error: () => {} });
    fixture.detectChanges();
    expect(activity.pending()).toBe(2);
    expect(fixture.nativeElement.querySelector('.request-progress').textContent).toContain(
      'Processando solicitação',
    );
    http.expectOne('/api/primeira').flush({});
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.request-progress')).not.toBeNull();
    http.expectOne('/api/segunda').flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(activity.pending()).toBe(0);
    expect(fixture.nativeElement.querySelector('.request-progress')).toBeNull();
  });

  it('remove progresso ao cancelar e não acompanha destinos externos', () => {
    const subscription = client.get('/api/cancelada').subscribe();
    const cancelled = http.expectOne('/api/cancelada');
    subscription.unsubscribe();
    expect(cancelled.cancelled).toBe(true);
    expect(activity.pending()).toBe(0);
    client.get('https://external.test').subscribe();
    expect(activity.pending()).toBe(0);
    http.expectOne('https://external.test').flush({});
  });

  it('preserva confirmação durante atualização de dados e limpa ao iniciar outra ação', () => {
    activity.sessionSuccess.set('Login realizado com sucesso.');
    client.get('/api/dados').subscribe();
    http.expectOne('/api/dados').flush({});
    expect(activity.sessionSuccess()).toContain('Login');
    client.post('/api/acao', {}).subscribe();
    expect(activity.sessionSuccess()).toBe('');
    http.expectOne('/api/acao').flush({});
  });

  it('limpa a confirmação da sessão ao navegar e a apresenta na aplicação', async () => {
    const fixture = TestBed.createComponent(App);
    activity.sessionSuccess.set('Você saiu da sua conta com segurança.');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.alert.success').textContent).toContain('saiu');
    await TestBed.inject(Router).navigateByUrl('/');
    fixture.detectChanges();
    expect(activity.sessionSuccess()).toBe('');
    expect(fixture.nativeElement.querySelector('.alert.success')).toBeNull();
  });
});
