"""Cria o modelo inicial e as restrições de integridade do MVP."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ExcludeConstraint

revision = "0001_modelo_inicial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.create_table(
        "administradores",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("senha_hash", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_administradores_email"),
        sa.CheckConstraint("length(btrim(nome)) > 0", name="ck_administradores_nome"),
        sa.CheckConstraint("length(btrim(email)) > 0", name="ck_administradores_email"),
        sa.CheckConstraint("length(btrim(senha_hash)) > 0", name="ck_administradores_senha_hash"),
    )
    op.create_table(
        "servicos",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("administrador_id", sa.Uuid(), sa.ForeignKey("administradores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("preco", sa.Numeric(10, 2), nullable=False),
        sa.Column("duracao_minutos", sa.Integer(), nullable=False),
        sa.Column("imagem_url", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("length(btrim(nome)) > 0", name="ck_servicos_nome"),
        sa.CheckConstraint("preco > 0 AND preco <> 'NaN'::numeric", name="ck_servicos_preco"),
        sa.CheckConstraint("duracao_minutos > 0", name="ck_servicos_duracao"),
    )
    op.create_index("ix_servicos_administrador_id", "servicos", ["administrador_id"])
    op.create_table(
        "horarios_disponiveis",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("administrador_id", sa.Uuid(), sa.ForeignKey("administradores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fim", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bloqueado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.CheckConstraint("fim > inicio", name="ck_horarios_intervalo"),
        ExcludeConstraint(
            ("administrador_id", "="),
            (sa.func.tstzrange(sa.column("inicio"), sa.column("fim"), "[)"), "&&"),
            name="ex_horarios_sem_sobreposicao", using="gist",
        ),
    )
    op.create_index("ix_horarios_administrador_inicio", "horarios_disponiveis", ["administrador_id", "inicio"])
    op.create_table(
        "agendamentos",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("servico_id", sa.Uuid(), sa.ForeignKey("servicos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("horario_id", sa.Uuid(), sa.ForeignKey("horarios_disponiveis.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cliente_nome", sa.String(150), nullable=False),
        sa.Column("cliente_telefone", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pendente'")),
        sa.Column("preco_solicitado", sa.Numeric(10, 2), nullable=False),
        sa.Column("duracao_minutos_solicitada", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("length(btrim(cliente_nome)) > 0", name="ck_agendamentos_nome"),
        sa.CheckConstraint("length(btrim(cliente_telefone)) > 0", name="ck_agendamentos_telefone"),
        sa.CheckConstraint("status IN ('pendente', 'aprovado', 'recusado', 'cancelado')", name="ck_agendamentos_status"),
        sa.CheckConstraint("preco_solicitado > 0 AND preco_solicitado <> 'NaN'::numeric", name="ck_agendamentos_preco_solicitado"),
        sa.CheckConstraint("duracao_minutos_solicitada > 0", name="ck_agendamentos_duracao_solicitada"),
    )
    op.create_index(
        "uq_agendamentos_horario_ativo", "agendamentos", ["horario_id"], unique=True,
        postgresql_where=sa.text("status IN ('pendente', 'aprovado')"),
    )
    op.create_index("ix_agendamentos_servico_id", "agendamentos", ["servico_id"])
    op.create_index("ix_agendamentos_horario_id", "agendamentos", ["horario_id"])

    op.execute("""
        CREATE FUNCTION public.validar_integridade_agendamento() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        DECLARE periodo interval; mesmo_administrador boolean;
        BEGIN
            IF TG_OP = 'UPDATE' AND (
                NEW.preco_solicitado IS DISTINCT FROM OLD.preco_solicitado OR
                NEW.duracao_minutos_solicitada IS DISTINCT FROM OLD.duracao_minutos_solicitada
            ) THEN
                RAISE EXCEPTION 'Valores históricos não podem ser alterados'
                    USING ERRCODE = '23514', CONSTRAINT = 'ck_agendamentos_historico';
            END IF;
            SELECT h.fim - h.inicio, h.administrador_id = s.administrador_id
                INTO periodo, mesmo_administrador
                FROM public.horarios_disponiveis h CROSS JOIN public.servicos s
                WHERE h.id = NEW.horario_id AND s.id = NEW.servico_id
                FOR SHARE OF h;
            IF FOUND THEN
                IF NOT mesmo_administrador THEN
                    RAISE EXCEPTION 'Serviço e horário pertencem a administradores diferentes'
                        USING ERRCODE = '23514', CONSTRAINT = 'ck_agendamentos_administrador';
                END IF;
                IF NEW.status IN ('pendente', 'aprovado') AND
                    NEW.duracao_minutos_solicitada * interval '1 minute' > periodo THEN
                    RAISE EXCEPTION 'Duração excede o bloco de horário'
                        USING ERRCODE = '23514', CONSTRAINT = 'ck_agendamentos_duracao_bloco';
                END IF;
            END IF;
            RETURN NEW;
        END $$
    """)
    op.execute("""
        CREATE TRIGGER trg_validar_agendamento BEFORE INSERT OR UPDATE ON public.agendamentos
        FOR EACH ROW EXECUTE FUNCTION public.validar_integridade_agendamento()
    """)
    op.execute("""
        CREATE FUNCTION public.validar_duracao_bloco() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM public.agendamentos
                WHERE horario_id = NEW.id AND status IN ('pendente', 'aprovado')
                  AND duracao_minutos_solicitada * interval '1 minute' > NEW.fim - NEW.inicio
            ) THEN
                RAISE EXCEPTION 'Bloco não comporta a reserva ativa'
                    USING ERRCODE = '23514', CONSTRAINT = 'ck_horarios_duracao_reserva';
            END IF;
            RETURN NEW;
        END $$
    """)
    op.execute("""
        CREATE TRIGGER trg_validar_duracao_bloco BEFORE UPDATE OF inicio, fim ON public.horarios_disponiveis
        FOR EACH ROW EXECUTE FUNCTION public.validar_duracao_bloco()
    """)
    op.execute("REVOKE ALL ON FUNCTION public.validar_integridade_agendamento() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION public.validar_duracao_bloco() FROM PUBLIC")
    for table in ("administradores", "servicos", "horarios_disponiveis", "agendamentos"):
        op.execute(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'REVOKE ALL ON TABLE public."{table}" FROM PUBLIC')
        op.execute(f"""
            DO $$ DECLARE papel text; BEGIN
                FOR papel IN SELECT rolname FROM pg_roles
                    WHERE rolname IN ('anon', 'authenticated', 'service_role') LOOP
                    EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I', '{table}', papel);
                END LOOP;
            END $$
        """)


def downgrade() -> None:
    op.execute("DROP TRIGGER trg_validar_duracao_bloco ON public.horarios_disponiveis")
    op.execute("DROP TRIGGER trg_validar_agendamento ON public.agendamentos")
    op.execute("DROP FUNCTION public.validar_duracao_bloco()")
    op.execute("DROP FUNCTION public.validar_integridade_agendamento()")
    op.drop_table("agendamentos")
    op.drop_table("horarios_disponiveis")
    op.drop_table("servicos")
    op.drop_table("administradores")
    # btree_gist é compartilhável; não remover a extensão ao desfazer esta revisão.
