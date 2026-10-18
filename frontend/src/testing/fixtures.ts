import { Service, Slot, Booking, AdminSession } from '../app/core/models';
export const SERVICE: Service = {
  id: 'service-1',
  nome: 'Box Braids',
  descricao: 'Tranças individuais longas',
  preco: '180.00',
  duracao_minutos: 240,
  imagem_url: null,
  ativo: true,
};
export const SLOT: Slot = {
  id: 'slot-1',
  inicio: '2030-10-30T17:00:00Z',
  fim: '2030-10-30T21:00:00Z',
  bloqueado: false,
};
export const SESSION: AdminSession = {
  nome: 'Administradora sintética',
  csrf_token: 'csrf-exclusivo-de-teste',
  expira_em: '2099-01-01T00:00:00Z',
};
export const BOOKING: Booking = {
  id: 'booking-1',
  servico_id: SERVICE.id,
  horario_id: SLOT.id,
  cliente_nome: 'Cliente sintética',
  cliente_telefone: '11999990000',
  status: 'pendente',
  preco_solicitado: '180.00',
  duracao_minutos_solicitada: 240,
  criado_em: '2030-10-01T12:00:00Z',
  servico_nome: SERVICE.nome,
  inicio: SLOT.inicio,
  fim: SLOT.fim,
};
