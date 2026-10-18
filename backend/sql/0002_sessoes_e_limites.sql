BEGIN;

-- Running upgrade 0001_modelo_inicial -> 0002_sessoes_e_limites

CREATE TABLE sessoes_administrativas (
    id UUID NOT NULL,
    administrador_id UUID NOT NULL,
    expira_em TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(administrador_id) REFERENCES administradores (id) ON DELETE CASCADE
);

CREATE INDEX ix_sessoes_administrativas_administrador_id ON sessoes_administrativas (administrador_id);

CREATE INDEX ix_sessoes_administrativas_expira_em ON sessoes_administrativas (expira_em);

CREATE TABLE limites_requisicoes (
    chave VARCHAR(64) NOT NULL,
    janela TIMESTAMP WITH TIME ZONE NOT NULL,
    tentativas INTEGER NOT NULL,
    PRIMARY KEY (chave),
    CONSTRAINT ck_limites_tentativas CHECK (tentativas > 0)
);

CREATE INDEX ix_limites_requisicoes_janela ON limites_requisicoes (janela);

ALTER TABLE public.sessoes_administrativas ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.sessoes_administrativas FROM PUBLIC;

DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='anon')
                THEN REVOKE ALL ON TABLE public.sessoes_administrativas FROM anon; END IF; END $$;

DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='authenticated')
                THEN REVOKE ALL ON TABLE public.sessoes_administrativas FROM authenticated; END IF; END $$;

DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='service_role')
                THEN REVOKE ALL ON TABLE public.sessoes_administrativas FROM service_role; END IF; END $$;

ALTER TABLE public.limites_requisicoes ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.limites_requisicoes FROM PUBLIC;

DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='anon')
                THEN REVOKE ALL ON TABLE public.limites_requisicoes FROM anon; END IF; END $$;

DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='authenticated')
                THEN REVOKE ALL ON TABLE public.limites_requisicoes FROM authenticated; END IF; END $$;

DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='service_role')
                THEN REVOKE ALL ON TABLE public.limites_requisicoes FROM service_role; END IF; END $$;

UPDATE alembic_version SET version_num='0002_sessoes_e_limites' WHERE alembic_version.version_num = '0001_modelo_inicial';

COMMIT;

