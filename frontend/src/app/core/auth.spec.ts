import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';
import { firstValueFrom, Observable } from 'rxjs';
import { Auth, authGuard, sessionInterceptor } from './auth';
import { SessionStore } from './session-store';
import { SESSION } from '../../testing/fixtures';

describe('Sessão e proteção HTTP', () => {
  let auth: Auth, store: SessionStore, http: HttpTestingController, client: HttpClient;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([sessionInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    auth = TestBed.inject(Auth);
    store = TestBed.inject(SessionStore);
    http = TestBed.inject(HttpTestingController);
    client = TestBed.inject(HttpClient);
  });
  afterEach(() => http.verify());
  it('login guarda apenas sessão e CSRF na memória e logout limpa o estado', () => {
    store.expired.set(true);
    auth.login('admin@example.test', 'senha').subscribe();
    const login = http.expectOne('/api/auth/login');
    expect(login.request.withCredentials).toBe(true);
    login.flush(SESSION);
    expect(store.session()).toEqual(SESSION);
    expect(store.expired()).toBe(false);
    auth.logout().subscribe();
    const logout = http.expectOne('/api/auth/logout');
    expect(logout.request.headers.get('X-CSRF-Token')).toBe(SESSION.csrf_token);
    logout.flush(null);
    expect(store.session()).toBeNull();
  });
  it('restaura a sessão por cookie após recarga e reutiliza somente se não expirada', () => {
    auth.restore().subscribe();
    http.expectOne('/api/auth/sessao').flush(SESSION);
    auth.restore().subscribe((v) => expect(v).toEqual(SESSION));
    http.expectNone('/api/auth/sessao');
    store.session.set({ ...SESSION, expira_em: '2000-01-01T00:00:00Z' });
    auth.restore().subscribe();
    http.expectOne('/api/auth/sessao').flush(SESSION);
  });
  it('não envia cookie nem CSRF a destinos externos, nem CSRF em GET', () => {
    store.session.set(SESSION);
    client.post('https://external.test/file', {}).subscribe();
    const external = http.expectOne('https://external.test/file');
    expect(external.request.withCredentials).toBe(false);
    expect(external.request.headers.has('X-CSRF-Token')).toBe(false);
    external.flush({});
    client.get('/api/admin/servicos').subscribe();
    const get = http.expectOne('/api/admin/servicos');
    expect(get.request.headers.has('X-CSRF-Token')).toBe(false);
    get.flush([]);
  });
  it('não inventa CSRF sem sessão', () => {
    client.post('/api/publico/agendamentos', {}).subscribe();
    const req = http.expectOne('/api/publico/agendamentos');
    expect(req.request.headers.has('X-CSRF-Token')).toBe(false);
    req.flush({});
  });
  it.each(['/api/admin/servicos', '/api/auth/logout'])(
    'expiração em %s limpa sessão e redireciona',
    (url) => {
      const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
      store.session.set(SESSION);
      client.post(url, {}).subscribe({ error: () => {} });
      http.expectOne(url).flush({}, { status: 401, statusText: 'Unauthorized' });
      expect(store.session()).toBeNull();
      expect(store.expired()).toBe(true);
      expect(navigate).toHaveBeenCalledWith('/login');
    },
  );
  it('falha de login não redireciona e outros erros não apagam sessão', () => {
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    auth.login('a@b.test', 'errada').subscribe({ error: () => {} });
    http.expectOne('/api/auth/login').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(store.expired()).toBe(false);
    expect(navigate).not.toHaveBeenCalled();
    store.session.set(SESSION);
    client.get('/api/admin/servicos').subscribe({ error: () => {} });
    http.expectOne('/api/admin/servicos').flush({}, { status: 503, statusText: 'Unavailable' });
    expect(store.session()).toEqual(SESSION);
  });
  it('falha de restauração marca expiração sem iniciar navegação recursiva', () => {
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    store.session.set({ ...SESSION, expira_em: '2000-01-01T00:00:00Z' });
    auth.restore().subscribe({ error: () => {} });
    http.expectOne('/api/auth/sessao').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(store.expired()).toBe(true);
    expect(navigate).not.toHaveBeenCalled();
  });
  it('primeiro acesso sem cookie não é apresentado como sessão expirada', () => {
    auth.restore().subscribe({ error: () => {} });
    http.expectOne('/api/auth/sessao').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(store.expired()).toBe(false);
  });
  it('guard permite sessão válida e produz rota de login sem sessão', async () => {
    store.session.set(SESSION);
    let result = TestBed.runInInjectionContext(() =>
      authGuard({} as never, {} as never),
    ) as Observable<boolean | UrlTree>;
    expect(await firstValueFrom(result)).toBe(true);
    store.clear();
    result = TestBed.runInInjectionContext(() => authGuard({} as never, {} as never)) as Observable<
      boolean | UrlTree
    >;
    const promise = firstValueFrom(result);
    http.expectOne('/api/auth/sessao').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(TestBed.inject(Router).serializeUrl((await promise) as UrlTree)).toBe('/login');
  });
});
