from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SessaoAdministrativa(Base):
    __tablename__ = 'sessoes_administrativas'
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    administrador_id: Mapped[UUID] = mapped_column(ForeignKey('administradores.id', ondelete='CASCADE'), index=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class LimiteRequisicao(Base):
    __tablename__ = 'limites_requisicoes'
    __table_args__ = (CheckConstraint('tentativas > 0', name='ck_limites_tentativas'),)
    chave: Mapped[str] = mapped_column(String(64), primary_key=True)
    janela: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    tentativas: Mapped[int] = mapped_column(Integer)
