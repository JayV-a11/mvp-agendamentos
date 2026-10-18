import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AgendaPage } from './agenda';
import { BOOKING, SLOT } from '../../../testing/fixtures';

describe('Agenda administrativa', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  function flush(bookings = [BOOKING], slots = [SLOT]) {
    http.expectOne((r) => r.url === '/api/admin/agendamentos').flush(bookings);
    http.expectOne((r) => r.url === '/api/admin/horarios').flush(slots);
    http.expectOne('/api/publico/configuracao').flush({ fuso_horario: 'America/Sao_Paulo' });
  }
  function loaded(bookings = [BOOKING], slots = [SLOT]) {
    const fixture = TestBed.createComponent(AgendaPage);
    flush(bookings, slots);
    fixture.detectChanges();
    return fixture;
  }
  it('mostra contatos somente na tela administrativa e filtra situações', () => {
    const fixture = loaded([BOOKING, { ...BOOKING, id: 'segundo', status: 'aprovado' }]),
      page = fixture.componentInstance;
    expect(page.pending()).toBe(1);
    expect(page.approved()).toBe(1);
    expect(fixture.nativeElement.textContent).toContain(BOOKING.cliente_telefone);
    page.filter.set('aprovado');
    fixture.detectChanges();
    expect(page.visibleBookings()).toHaveLength(1);
    expect(fixture.nativeElement.textContent).toContain('Atendimento confirmado');
    page.filter.set('cancelado');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Nenhuma solicitação nesta situação');
  });
  it('mostra estados vazios e abre formulário de horário', () => {
    const fixture = loaded([], []);
    expect(fixture.nativeElement.textContent).toContain('Nenhum horário cadastrado');
    fixture.nativeElement.querySelector('button').click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('#slot-start')).not.toBeNull();
    fixture.componentInstance.createSlot();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Informe a data e a hora');
    http.expectNone('/api/admin/horarios');
  });
  it.each([
    ['2000-01-01T10:00', '2000-01-01T11:00'],
    ['2030-10-30T14:00', '2030-10-30T13:00'],
    ['inválido', '2030-10-30T13:00'],
  ])('rejeita intervalo %s / %s', (inicio, fim) => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.form.setValue({ inicio, fim });
    page.createSlot();
    expect(page.error()).toContain('início futuro');
    http.expectNone('/api/admin/horarios');
  });
  it('converte horário do negócio, evita envio duplicado e atualiza agenda', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.form.setValue({ inicio: '2030-10-30T14:00', fim: '2030-10-30T18:00' });
    page.createSlot();
    page.createSlot();
    const req = http.expectOne('/api/admin/horarios');
    expect(req.request.body).toEqual({
      inicio: '2030-10-30T17:00:00.000Z',
      fim: '2030-10-30T21:00:00.000Z',
    });
    req.flush(SLOT);
    flush();
    expect(page.success()).toContain('disponibilizado');
    expect(page.form.controls.inicio.value).toBe('');
  });
  it('sobreposição recebe mensagem de conflito sem adicionar bloco fictício', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.form.setValue({ inicio: '2030-10-30T14:00', fim: '2030-10-30T18:00' });
    page.createSlot();
    http.expectOne('/api/admin/horarios').flush({}, { status: 409, statusText: 'Conflict' });
    expect(page.error()).toContain('alterados');
    expect(page.busy()).toBe(false);
  });
  it.each(['aprovado', 'recusado', 'cancelado'] as const)(
    'atualiza estado %s apenas após confirmação da API',
    (status) => {
      const other = { ...BOOKING, id: 'outro', horario_id: 'outro' };
      const fixture = loaded([BOOKING, other]),
        page = fixture.componentInstance;
      page.decide(BOOKING, status);
      page.decide(BOOKING, status);
      expect(page.bookings()[0].status).toBe('pendente');
      http.expectOne(`/api/admin/agendamentos/${BOOKING.id}/status`).flush({ ...BOOKING, status });
      fixture.detectChanges();
      expect(page.bookings()[0].status).toBe(status);
      expect(page.bookings()[1]).toEqual(other);
      expect(page.success()).toContain(status);
    },
  );
  it('decisão conflitante preserva estado e permite atualização manual', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.decide(BOOKING, 'aprovado');
    http
      .expectOne(`/api/admin/agendamentos/${BOOKING.id}/status`)
      .flush({}, { status: 409, statusText: 'Conflict' });
    expect(page.bookings()[0].status).toBe('pendente');
    expect(page.error()).not.toBe('');
  });
  it.each([true, false])('altera bloqueado=%s após resposta da API', (bloqueado) => {
    const fixture = loaded(
        [],
        [
          { ...SLOT, bloqueado },
          { ...SLOT, id: 'outro' },
        ],
      ),
      page = fixture.componentInstance;
    page.block({ ...SLOT, bloqueado });
    page.block(SLOT);
    http
      .expectOne(`/api/admin/horarios/${SLOT.id}/bloqueio`)
      .flush({ ...SLOT, bloqueado: !bloqueado });
    expect(page.slots()[0].bloqueado).toBe(!bloqueado);
    expect(page.slots()[1].id).toBe('outro');
    expect(page.success()).toContain(bloqueado ? 'desbloqueado' : 'bloqueado');
  });
  it('trata falha no bloqueio sem atualizar estado local', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.block(SLOT);
    http
      .expectOne(`/api/admin/horarios/${SLOT.id}/bloqueio`)
      .flush({}, { status: 503, statusText: 'Unavailable' });
    expect(page.slots()[0].bloqueado).toBe(false);
    expect(page.error()).not.toBe('');
    expect(page.busy()).toBe(false);
  });
  it('distingue bloqueado, reservado, livre e encerrado sem liberar reserva ativa', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    expect(page.slotState({ ...SLOT, bloqueado: true })).toBe('Bloqueado');
    expect(page.slotState(SLOT)).toBe('Reservado');
    page.bookings.set([{ ...BOOKING, status: 'recusado' }]);
    expect(page.slotState(SLOT)).toBe('Livre');
    expect(page.slotState({ ...SLOT, inicio: '2000-01-01T00:00:00Z' })).toBe('Encerrado');
  });
  it('trata falha no carregamento sem afirmar que a agenda está vazia', () => {
    const fixture = TestBed.createComponent(AgendaPage);
    http.match(() => true)[0].flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(fixture.componentInstance.loading()).toBe(false);
    expect(fixture.nativeElement.querySelector('[role=alert]')).not.toBeNull();
  });
});
