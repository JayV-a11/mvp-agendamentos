BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_modelo_inicial

CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE administradores (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    senha_hash TEXT NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_administradores_email UNIQUE (email),
    CONSTRAINT ck_administradores_nome CHECK (length(btrim(nome)) > 0),
    CONSTRAINT ck_administradores_email CHECK (length(btrim(email)) > 0),
    CONSTRAINT ck_administradores_senha_hash CHECK (length(btrim(senha_hash)) > 0)
);

CREATE TABLE servicos (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    administrador_id UUID NOT NULL,
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    preco NUMERIC(10, 2) NOT NULL,
    duracao_minutos INTEGER NOT NULL,
    imagem_url TEXT,
    ativo BOOLEAN DEFAULT true NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_servicos_nome CHECK (length(btrim(nome)) > 0),
    CONSTRAINT ck_servicos_preco CHECK (preco > 0 AND preco <> 'NaN'::numeric),
    CONSTRAINT ck_servicos_duracao CHECK (duracao_minutos > 0),
    FOREIGN KEY(administrador_id) REFERENCES administradores (id) ON DELETE RESTRICT
);

CREATE INDEX ix_servicos_administrador_id ON servicos (administrador_id);

CREATE TABLE horarios_disponiveis (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    administrador_id UUID NOT NULL,
    inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fim TIMESTAMP WITH TIME ZONE NOT NULL,
    bloqueado BOOLEAN DEFAULT false NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_horarios_intervalo CHECK (fim > inicio),
    CONSTRAINT ex_horarios_sem_sobreposicao EXCLUDE USING gist (administrador_id WITH =, tstzrange(inicio, fim, '[)') WITH &&),
    FOREIGN KEY(administrador_id) REFERENCES administradores (id) ON DELETE RESTRICT
);

CREATE INDEX ix_horarios_administrador_inicio ON horarios_disponiveis (administrador_id, inicio);

CREATE TABLE agendamentos (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    servico_id UUID NOT NULL,
    horario_id UUID NOT NULL,
    cliente_nome VARCHAR(150) NOT NULL,
    cliente_telefone VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente' NOT NULL,
    preco_solicitado NUMERIC(10, 2) NOT NULL,
    duracao_minutos_solicitada INTEGER NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_agendamentos_nome CHECK (length(btrim(cliente_nome)) > 0),
    CONSTRAINT ck_agendamentos_telefone CHECK (length(btrim(cliente_telefone)) > 0),
    CONSTRAINT ck_agendamentos_status CHECK (status IN ('pendente', 'aprovado', 'recusado', 'cancelado')),
    CONSTRAINT ck_agendamentos_preco_solicitado CHECK (preco_solicitado > 0 AND preco_solicitado <> 'NaN'::numeric),
    CONSTRAINT ck_agendamentos_duracao_solicitada CHECK (duracao_minutos_solicitada > 0),
    FOREIGN KEY(servico_id) REFERENCES servicos (id) ON DELETE RESTRICT,
    FOREIGN KEY(horario_id) REFERENCES horarios_disponiveis (id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_agendamentos_horario_ativo ON agendamentos (horario_id) WHERE status IN ('pendente', 'aprovado');

CREATE INDEX ix_agendamentos_servico_id ON agendamentos (servico_id);

CREATE INDEX ix_agendamentos_horario_id ON agendamentos (horario_id);

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
        END $$;

CREATE TRIGGER trg_validar_agendamento BEFORE INSERT OR UPDATE ON public.agendamentos
        FOR EACH ROW EXECUTE FUNCTION public.validar_integridade_agendamento();

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
        END $$;

CREATE TRIGGER trg_validar_duracao_bloco BEFORE UPDATE OF inicio, fim ON public.horarios_disponiveis
        FOR EACH ROW EXECUTE FUNCTION public.validar_duracao_bloco();

REVOKE ALL ON FUNCTION public.validar_integridade_agendamento() FROM PUBLIC;

REVOKE ALL ON FUNCTION public.validar_duracao_bloco() FROM PUBLIC;

ALTER TABLE public."administradores" ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public."administradores" FROM PUBLIC;

DO $$ DECLARE papel text; BEGIN
                FOR papel IN SELECT rolname FROM pg_roles
                    WHERE rolname IN ('anon', 'authenticated', 'service_role') LOOP
                    EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I', 'administradores', papel);
                END LOOP;
            END $$;

ALTER TABLE public."servicos" ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public."servicos" FROM PUBLIC;

DO $$ DECLARE papel text; BEGIN
                FOR papel IN SELECT rolname FROM pg_roles
                    WHERE rolname IN ('anon', 'authenticated', 'service_role') LOOP
                    EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I', 'servicos', papel);
                END LOOP;
            END $$;

ALTER TABLE public."horarios_disponiveis" ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public."horarios_disponiveis" FROM PUBLIC;

DO $$ DECLARE papel text; BEGIN
                FOR papel IN SELECT rolname FROM pg_roles
                    WHERE rolname IN ('anon', 'authenticated', 'service_role') LOOP
                    EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I', 'horarios_disponiveis', papel);
                END LOOP;
            END $$;

ALTER TABLE public."agendamentos" ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public."agendamentos" FROM PUBLIC;

DO $$ DECLARE papel text; BEGIN
                FOR papel IN SELECT rolname FROM pg_roles
                    WHERE rolname IN ('anon', 'authenticated', 'service_role') LOOP
                    EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I', 'agendamentos', papel);
                END LOOP;
            END $$;

INSERT INTO alembic_version (version_num) VALUES ('0001_modelo_inicial') RETURNING alembic_version.version_num;

COMMIT;

