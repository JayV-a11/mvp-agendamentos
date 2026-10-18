import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { routes } from './app.routes';
import { sessionInterceptor } from './core/auth';
import { SessionStore } from './core/session-store';
import { SERVICE, SLOT, SESSION } from '../testing/fixtures';

describe('Rotas e navegação integrada dos componentes', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes),
        provideHttpClient(withInterceptors([sessionInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  async function flush(path: string, value: object) {
    const req = await vi.waitFor(() => http.expectOne((r) => r.url === path));
    req.flush(value);
  }
  it('navega entre catálogo, solicitação, login e administração protegida', async () => {
    const harness = await RouterTestingHarness.create();
    let navigation = harness.navigateByUrl('/');
    await flush('/api/publico/servicos', [SERVICE]);
    await navigation;
    expect(harness.routeNativeElement?.textContent).toContain('Encontre seu próximo estilo');
    navigation = harness.navigateByUrl(`/agendar/${SERVICE.id}`);
    await flush(`/api/publico/servicos/${SERVICE.id}`, SERVICE);
    await flush(`/api/publico/servicos/${SERVICE.id}/horarios`, [SLOT]);
    await flush('/api/publico/configuracao', { fuso_horario: 'America/Sao_Paulo' });
    await navigation;
    expect(harness.routeNativeElement?.textContent).toContain('Solicitar agendamento');
    await harness.navigateByUrl('/login');
    expect(harness.routeNativeElement?.textContent).toContain('Bem-vinda de volta');
    TestBed.inject(SessionStore).session.set(SESSION);
    navigation = harness.navigateByUrl('/admin/agenda');
    await flush('/api/admin/agendamentos', []);
    await flush('/api/admin/horarios', []);
    await flush('/api/publico/configuracao', { fuso_horario: 'America/Sao_Paulo' });
    await navigation;
    expect(harness.routeNativeElement?.textContent).toContain('Minha agenda');
    navigation = harness.navigateByUrl('/admin/servicos');
    await flush('/api/admin/servicos', []);
    await navigation;
    expect(harness.routeNativeElement?.textContent).toContain('Gerenciar catálogo');
    navigation = harness.navigateByUrl('/admin');
    await flush('/api/admin/agendamentos', []);
    await flush('/api/admin/horarios', []);
    await flush('/api/publico/configuracao', { fuso_horario: 'America/Sao_Paulo' });
    await navigation;
    navigation = harness.navigateByUrl('/inexistente');
    await flush('/api/publico/servicos', []);
    await navigation;
    harness.detectChanges();
    expect(harness.routeNativeElement?.textContent).toContain('Nenhum serviço disponível');
  });
  it('bloqueia entrada administrativa direta sem sessão', async () => {
    const harness = await RouterTestingHarness.create();
    const navigation = harness.navigateByUrl('/admin/agenda');
    const req = await vi.waitFor(() => http.expectOne('/api/auth/sessao'));
    req.flush({}, { status: 401, statusText: 'Unauthorized' });
    await navigation;
    expect(harness.routeNativeElement?.textContent).toContain('Bem-vinda de volta');
    http.expectNone((r) => r.url.startsWith('/api/admin/'));
  });
});
