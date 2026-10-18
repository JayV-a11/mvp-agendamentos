from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric,
    String, Text, UniqueConstraint, Uuid, func, text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Administrador(Base):
    __tablename__ = "administradores"
    __table_args__ = (
        UniqueConstraint("email", name="uq_administradores_email"),
        CheckConstraint("length(btrim(nome)) > 0", name="ck_administradores_nome"),
        CheckConstraint("length(btrim(email)) > 0", name="ck_administradores_email"),
        CheckConstraint("length(btrim(senha_hash)) > 0", name="ck_administradores_senha_hash"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    senha_hash: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Servico(Base):
    __tablename__ = "servicos"
    __table_args__ = (
        CheckConstraint("length(btrim(nome)) > 0", name="ck_servicos_nome"),
        CheckConstraint("preco > 0 AND preco <> 'NaN'::numeric", name="ck_servicos_preco"),
        CheckConstraint("duracao_minutos > 0", name="ck_servicos_duracao"),
        Index("ix_servicos_administrador_id", "administrador_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    administrador_id: Mapped[UUID] = mapped_column(ForeignKey("administradores.id", ondelete="RESTRICT"))
    nome: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str | None] = mapped_column(Text)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    duracao_minutos: Mapped[int] = mapped_column(Integer)
    imagem_url: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class HorarioDisponivel(Base):
    __tablename__ = "horarios_disponiveis"
    __table_args__ = (
        CheckConstraint("fim > inicio", name="ck_horarios_intervalo"),
        ExcludeConstraint(
            ("administrador_id", "="),
            (func.tstzrange(text("inicio"), text("fim"), "[)"), "&&"),
            name="ex_horarios_sem_sobreposicao",
            using="gist",
        ),
        Index("ix_horarios_administrador_inicio", "administrador_id", "inicio"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    administrador_id: Mapped[UUID] = mapped_column(ForeignKey("administradores.id", ondelete="RESTRICT"))
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    bloqueado: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))


class Agendamento(Base):
    __tablename__ = "agendamentos"
    __table_args__ = (
        CheckConstraint("length(btrim(cliente_nome)) > 0", name="ck_agendamentos_nome"),
        CheckConstraint("length(btrim(cliente_telefone)) > 0", name="ck_agendamentos_telefone"),
        CheckConstraint(
            "status IN ('pendente', 'aprovado', 'recusado', 'cancelado')",
            name="ck_agendamentos_status",
        ),
        CheckConstraint("preco_solicitado > 0 AND preco_solicitado <> 'NaN'::numeric", name="ck_agendamentos_preco_solicitado"),
        CheckConstraint("duracao_minutos_solicitada > 0", name="ck_agendamentos_duracao_solicitada"),
        Index(
            "uq_agendamentos_horario_ativo", "horario_id", unique=True,
            postgresql_where=text("status IN ('pendente', 'aprovado')"),
        ),
        Index("ix_agendamentos_servico_id", "servico_id"),
        Index("ix_agendamentos_horario_id", "horario_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    servico_id: Mapped[UUID] = mapped_column(ForeignKey("servicos.id", ondelete="RESTRICT"))
    horario_id: Mapped[UUID] = mapped_column(ForeignKey("horarios_disponiveis.id", ondelete="RESTRICT"))
    cliente_nome: Mapped[str] = mapped_column(String(150))
    cliente_telefone: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'pendente'"))
    preco_solicitado: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    duracao_minutos_solicitada: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
