import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, hide_input_in_errors=True)


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def normalize_email(value):
    value = value.strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
        raise ValueError('Informe um e-mail válido.')
    return value


class Login(Input):
    email: str = Field(min_length=3, max_length=255)
    senha: str = Field(min_length=1, max_length=128, json_schema_extra={'format': 'password'})
    # Senhas não são aparadas: espaços podem fazer parte da credencial.
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    _email = field_validator('email')(normalize_email)


class AdminCreate(Input):
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    _email = field_validator('email')(normalize_email)


class SessionOutput(Output):
    nome: str
    csrf_token: str
    expira_em: datetime


class ServiceInput(Input):
    nome: str = Field(min_length=1, max_length=150)
    descricao: str | None = Field(default=None, max_length=5000)
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2, allow_inf_nan=False)
    duracao_minutos: int = Field(gt=0, le=2147483647, strict=True)
    ativo: bool = True


class ServiceOutput(Output):
    id: UUID
    nome: str
    descricao: str | None
    preco: Decimal
    duracao_minutos: int
    imagem_url: str | None
    ativo: bool


class SlotInput(Input):
    inicio: AwareDatetime
    fim: AwareDatetime

    @model_validator(mode='after')
    def interval(self):
        if self.fim <= self.inicio:
            raise ValueError('O fim deve ser posterior ao início.')
        return self


class BlockInput(Input):
    bloqueado: bool


class SlotOutput(Output):
    id: UUID
    inicio: datetime
    fim: datetime
    bloqueado: bool


class BookingInput(Input):
    servico_id: UUID
    horario_id: UUID
    cliente_nome: str = Field(min_length=1, max_length=150)
    cliente_telefone: str = Field(min_length=8, max_length=30)

    @field_validator('cliente_telefone')
    @classmethod
    def phone(cls, value):
        if not re.fullmatch(r'\+?[0-9 ()-]+', value):
            raise ValueError('Informe um telefone válido com código de área.')
        number = re.sub(r'[ ()-]', '', value)
        if not 10 <= len(number.lstrip('+')) <= 15:
            raise ValueError('O telefone deve conter entre 10 e 15 dígitos.')
        return number


Status = Literal['pendente', 'aprovado', 'recusado', 'cancelado']


class StatusInput(Input):
    status: Literal['aprovado', 'recusado', 'cancelado']


class BookingConfirmation(Output):
    id: UUID
    status: Status
    mensagem: str = 'Solicitação recebida e pendente de aprovação pela profissional.'


class BookingOutput(Output):
    id: UUID
    servico_id: UUID
    horario_id: UUID
    cliente_nome: str
    cliente_telefone: str
    status: Status
    preco_solicitado: Decimal
    duracao_minutos_solicitada: int
    criado_em: datetime
    servico_nome: str
    inicio: datetime
    fim: datetime
