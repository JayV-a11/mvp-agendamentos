import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BookingPage } from './booking';
import { SERVICE, SLOT } from '../../../testing/fixtures';

describe('Solicitação pública', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id: SERVICE.id }) } },
        },
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  function loaded(slots = [SLOT]) {
    const fixture = TestBed.createComponent(BookingPage);
    http.expectOne(`/api/publico/servicos/${SERVICE.id}`).flush(SERVICE);
    http.expectOne((r) => r.url.endsWith('/horarios')).flush(slots);
    http.expectOne('/api/publico/configuracao').flush({ fuso_horario: 'America/Sao_Paulo' });
    fixture.detectChanges();
    return fixture;
  }
  it('exibe serviço, datas e blocos no fuso do negócio, com seleção acessível', () => {
    const fixture = loaded([
      SLOT,
      { ...SLOT, id: 'outro', inicio: '2030-10-31T17:00:00Z', fim: '2030-10-31T21:00:00Z' },
    ]);
    expect(fixture.nativeElement.textContent).toContain('14:00');
    expect(fixture.componentInstance.days()).toEqual(['2030-10-30', '2030-10-31']);
    const button = fixture.nativeElement.querySelector('.slot-button');
    button.click();
    fixture.detectChanges();
    expect(button.getAttribute('aria-pressed')).toBe('true');
    const select = fixture.nativeElement.querySelector('select');
    select.value = '2030-10-31';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    expect(fixture.componentInstance.selected()).toBe('');
    expect(fixture.componentInstance.visibleSlots()[0].id).toBe('outro');
  });
  it('valida nome, telefone e horário antes de enviar', () => {
    const fixture = loaded();
    fixture.componentInstance.submit();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Informe seu nome');
    expect(fixture.nativeElement.textContent).toContain('DDD');
    http.expectNone('/api/publico/agendamentos');
    fixture.componentInstance.form.setValue({
      cliente_nome: 'Cliente',
      cliente_telefone: '11999990000',
    });
    fixture.componentInstance.submit();
    expect(fixture.componentInstance.error()).toContain('selecione um horário');
    fixture.nativeElement
      .querySelector('#client-name')
      .dispatchEvent(new Event('input', { bubbles: true }));
    expect(fixture.componentInstance.error()).toBe('');
  });
  it('envia uma vez, limpa dados pessoais e apresenta confirmação pendente', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.form.setValue({ cliente_nome: 'Cliente', cliente_telefone: '11999990000' });
    page.selected.set(SLOT.id);
    page.submit();
    page.submit();
    const req = http.expectOne('/api/publico/agendamentos');
    expect(req.request.body).toEqual({
      servico_id: SERVICE.id,
      horario_id: SLOT.id,
      cliente_nome: 'Cliente',
      cliente_telefone: '11999990000',
    });
    req.flush({ id: 'pedido', status: 'pendente', mensagem: 'Pendente' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Status: Pendente');
    expect(fixture.nativeElement.querySelector('form')).toBeNull();
    expect(page.form.getRawValue().cliente_telefone).toBe('');
    page.submit();
    http.expectNone('/api/publico/agendamentos');
  });
  it('conflito limpa seleção e permite atualização da disponibilidade', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.form.setValue({ cliente_nome: 'Cliente', cliente_telefone: '11999990000' });
    page.selected.set(SLOT.id);
    page.submit();
    http.expectOne('/api/publico/agendamentos').flush({}, { status: 409, statusText: 'Conflict' });
    fixture.detectChanges();
    expect(page.selected()).toBe('');
    expect(page.busy()).toBe(false);
    expect(fixture.nativeElement.querySelector('[role=alert]')).not.toBeNull();
    page.load();
    http.expectOne(`/api/publico/servicos/${SERVICE.id}`).flush(SERVICE);
    http.expectOne((r) => r.url.endsWith('/horarios')).flush([]);
    http.expectOne('/api/publico/configuracao').flush({ fuso_horario: 'America/Sao_Paulo' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Não há horários disponíveis');
  });
  it('trata falha inicial sem mostrar formulário incompleto', () => {
    const fixture = TestBed.createComponent(BookingPage);
    const requests = http.match(() => true);
    requests[0].flush({}, { status: 404, statusText: 'Not found' });
    fixture.detectChanges();
    expect(fixture.componentInstance.loading()).toBe(false);
    expect(fixture.nativeElement.querySelector('form')).toBeNull();
    expect(fixture.nativeElement.querySelector('[role=alert]')).not.toBeNull();
  });
  it('trata disponibilidade vazia sem selecionar datas inexistentes', () => {
    const fixture = loaded([]);
    expect(fixture.componentInstance.day()).toBe('');
    expect(fixture.nativeElement.querySelector('form')).toBeNull();
  });
});
