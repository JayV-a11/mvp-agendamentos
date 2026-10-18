"""Estado técnico de sessões revogáveis e limites persistentes."""
from alembic import op
import sqlalchemy as sa

revision = '0002_sessoes_e_limites'
down_revision = '0001_modelo_inicial'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sessoes_administrativas',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('administrador_id', sa.Uuid(), sa.ForeignKey('administradores.id', ondelete='CASCADE'), nullable=False),
        sa.Column('expira_em', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_sessoes_administrativas_administrador_id', 'sessoes_administrativas', ['administrador_id'])
    op.create_index('ix_sessoes_administrativas_expira_em', 'sessoes_administrativas', ['expira_em'])
    op.create_table('limites_requisicoes',
        sa.Column('chave', sa.String(64), primary_key=True),
        sa.Column('janela', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tentativas', sa.Integer(), nullable=False),
        sa.CheckConstraint('tentativas > 0', name='ck_limites_tentativas'))
    op.create_index('ix_limites_requisicoes_janela', 'limites_requisicoes', ['janela'])
    for table in ('sessoes_administrativas', 'limites_requisicoes'):
        op.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY')
        op.execute(f'REVOKE ALL ON TABLE public.{table} FROM PUBLIC')
        for role in ('anon', 'authenticated', 'service_role'):
            op.execute(f"""DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='{role}')
                THEN REVOKE ALL ON TABLE public.{table} FROM {role}; END IF; END $$""")


def downgrade():
    op.drop_table('limites_requisicoes')
    op.drop_table('sessoes_administrativas')
