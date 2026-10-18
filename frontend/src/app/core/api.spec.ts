import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Api } from './api';
import { SERVICE, SLOT, BOOKING } from '../../testing/fixtures';

describe('Api — contratos HTTP', () => {
  let api: Api, http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(Api);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  it('carrega todas as páginas sem truncar a listagem', () => {
    let items: unknown[] = [];
    api.services().subscribe((value) => (items = value));
    const first = http.expectOne((r) => r.url === '/api/publico/servicos');
    expect(first.request.params.get('inicio')).toBe('0');
    expect(first.request.params.get('limite')).toBe('100');
    first.flush(Array.from({ length: 100 }, () => SERVICE));
    const second = http.expectOne((r) => r.url === '/api/publico/servicos');
    expect(second.request.params.get('inicio')).toBe('100');
    second.flush([SERVICE]);
    expect(items).toHaveLength(101);
  });
  it('consulta configuração, serviço selecionado e sua disponibilidade', () => {
    api.config().subscribe((v) => expect(v.fuso_horario).toBe('America/Sao_Paulo'));
    http.expectOne('/api/publico/configuracao').flush({ fuso_horario: 'America/Sao_Paulo' });
    api.service('id/com barra').subscribe();
    http.expectOne('/api/publico/servicos/id%2Fcom%20barra').flush(SERVICE);
    api.availability(SERVICE.id).subscribe((v) => expect(v).toEqual([SLOT]));
    http.expectOne((r) => r.url === `/api/publico/servicos/${SERVICE.id}/horarios`).flush([SLOT]);
  });
  it('cria apenas os campos públicos autorizados', () => {
    const data = {
      servico_id: SERVICE.id,
      horario_id: SLOT.id,
      cliente_nome: 'Cliente',
      cliente_telefone: '11999990000',
    };
    api.request(data).subscribe();
    const req = http.expectOne('/api/publico/agendamentos');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(data);
    req.flush({ id: 'id', status: 'pendente', mensagem: 'Pendente' });
  });
  it('consulta listagens administrativas e filtro de status', () => {
    api.services(true).subscribe();
    http.expectOne((r) => r.url === '/api/admin/servicos').flush([]);
    api.slots().subscribe();
    http.expectOne((r) => r.url === '/api/admin/horarios').flush([]);
    api.bookings().subscribe();
    http.expectOne((r) => r.url === '/api/admin/agendamentos' && !r.params.has('status')).flush([]);
    api.bookings('pendente').subscribe();
    http.expectOne((r) => r.params.get('status') === 'pendente').flush([BOOKING]);
  });
  it('cria e altera serviços sem enviar campos de propriedade ou histórico', () => {
    const data = {
      nome: SERVICE.nome,
      descricao: null,
      preco: '180',
      duracao_minutos: 240,
      ativo: true,
    };
    api.saveService(data).subscribe();
    let req = http.expectOne('/api/admin/servicos');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(data);
    req.flush(SERVICE);
    api.saveService(data, SERVICE.id).subscribe();
    req = http.expectOne(`/api/admin/servicos/${SERVICE.id}`);
    expect(req.request.method).toBe('PUT');
    req.flush(SERVICE);
  });
  it('envia bytes da foto com MIME e permite remoção', () => {
    const file = new File(['foto'], 'foto.png', { type: 'image/png' });
    api.upload(SERVICE.id, file).subscribe();
    const req = http.expectOne(`/api/admin/servicos/${SERVICE.id}/foto`);
    expect(req.request.body).toBe(file);
    expect(req.request.headers.get('Content-Type')).toBe('image/png');
    req.flush(SERVICE);
    api.removePhoto(SERVICE.id).subscribe();
    const remove = http.expectOne(`/api/admin/servicos/${SERVICE.id}/foto`);
    expect(remove.request.method).toBe('DELETE');
    remove.flush(SERVICE);
  });
  it('cria blocos, bloqueia e decide solicitações pelos contratos existentes', () => {
    api.createSlot(SLOT.inicio, SLOT.fim).subscribe();
    const create = http.expectOne('/api/admin/horarios');
    expect(create.request.body).toEqual({ inicio: SLOT.inicio, fim: SLOT.fim });
    create.flush(SLOT);
    api.block(SLOT.id, true).subscribe();
    const block = http.expectOne(`/api/admin/horarios/${SLOT.id}/bloqueio`);
    expect(block.request.body).toEqual({ bloqueado: true });
    block.flush({ ...SLOT, bloqueado: true });
    api.decide(BOOKING.id, 'aprovado').subscribe();
    const decide = http.expectOne(`/api/admin/agendamentos/${BOOKING.id}/status`);
    expect(decide.request.body).toEqual({ status: 'aprovado' });
    decide.flush({ ...BOOKING, status: 'aprovado' });
  });
});
