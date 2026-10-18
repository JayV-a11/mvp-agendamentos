export interface Service {
  id: string;
  nome: string;
  descricao: string | null;
  preco: string;
  duracao_minutos: number;
  imagem_url: string | null;
  ativo: boolean;
}
export type ServiceInput = Omit<Service, 'id' | 'imagem_url'>;
export interface Slot {
  id: string;
  inicio: string;
  fim: string;
  bloqueado: boolean;
}
export type Status = 'pendente' | 'aprovado' | 'recusado' | 'cancelado';
export interface Booking {
  id: string;
  servico_id: string;
  horario_id: string;
  cliente_nome: string;
  cliente_telefone: string;
  status: Status;
  preco_solicitado: string;
  duracao_minutos_solicitada: number;
  criado_em: string;
  servico_nome: string;
  inicio: string;
  fim: string;
}
export interface BookingInput {
  servico_id: string;
  horario_id: string;
  cliente_nome: string;
  cliente_telefone: string;
}
export interface Confirmation {
  id: string;
  status: Status;
  mensagem: string;
}
export interface AdminSession {
  nome: string;
  csrf_token: string;
  expira_em: string;
}
