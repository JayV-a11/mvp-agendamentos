import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Catalog } from './catalog';
import { SERVICE } from '../../../testing/fixtures';

describe('Catálogo público', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  it('apresenta nomes e descrições como texto, sem executar HTML recebido', () => {
    const fixture = TestBed.createComponent(Catalog);
    http
      .expectOne((r) => r.url === '/api/publico/servicos')
      .flush([
        {
          ...SERVICE,
          nome: '<script>alert(1)</script>',
          descricao: '<img src=x onerror=alert(1)>',
        },
      ]);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('script')).toBeNull();
    expect(fixture.nativeElement.querySelector('img')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('<script>');
  });
  it('mostra carregamento, serviço real recebido e link de agendamento', () => {
    const fixture = TestBed.createComponent(Catalog);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Carregando');
    http.expectOne((r) => r.url === '/api/publico/servicos').flush([SERVICE]);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('180,00');
    expect(fixture.nativeElement.textContent).toContain('4h');
    expect(fixture.nativeElement.querySelector('.service-card a').getAttribute('href')).toBe(
      '/agendar/service-1',
    );
  });
  it('mostra catálogo vazio sem dados fictícios', () => {
    const fixture = TestBed.createComponent(Catalog);
    http.expectOne((r) => r.url === '/api/publico/servicos').flush([]);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Nenhum serviço disponível');
    expect(fixture.nativeElement.querySelector('article')).toBeNull();
  });
  it('permite repetir após falha de rede', () => {
    const fixture = TestBed.createComponent(Catalog);
    http.expectOne((r) => r.url === '/api/publico/servicos').error(new ProgressEvent('error'));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=alert]')).not.toBeNull();
    fixture.nativeElement.querySelector('button.text-button').click();
    http
      .expectOne((r) => r.url === '/api/publico/servicos')
      .flush([{ ...SERVICE, descricao: null }]);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('article').length).toBe(1);
  });
});
