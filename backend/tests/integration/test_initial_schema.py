from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.models import Administrador, Agendamento, HorarioDisponivel, Servico
from tests.integration.conftest import migration_config

pytestmark = pytest.mark.integration


@pytest.fixture
def seed(db):
    start = datetime(2030, 1, 1, 10, tzinfo=timezone.utc)
    with db.begin() as connection:
        administrator = connection.execute(insert(Administrador).values(
            nome="Administradora sintética", email="admin@example.test",
            senha_hash="hash_sintetico_exclusivo_para_testes",
        ).returning(Administrador.id)).scalar_one()
        service = connection.execute(insert(Servico).values(
            administrador_id=administrator, nome="Serviço sintético",
            preco=Decimal("125.50"), duracao_minutos=60,
        ).returning(Servico.id)).scalar_one()
        slot = connection.execute(insert(HorarioDisponivel).values(
            administrador_id=administrator, inicio=start, fim=start + timedelta(hours=2),
        ).returning(HorarioDisponivel.id)).scalar_one()
    return {"admin": administrator, "service": service, "slot": slot, "start": start}


def booking_values(seed, **overrides):
    return {
        "servico_id": seed["service"], "horario_id": seed["slot"],
        "cliente_nome": "Cliente sintética", "cliente_telefone": "11999990000",
        "preco_solicitado": Decimal("125.50"), "duracao_minutos_solicitada": 60,
        **overrides,
    }


def test_defaults_uuid_decimal_e_timezone(db, seed):
    with db.begin() as connection:
        booking = connection.execute(insert(Agendamento).values(
            **booking_values(seed)
        ).returning(Agendamento.__table__)).mappings().one()
        service = connection.execute(select(Servico.__table__)).mappings().one()
        slot = connection.execute(select(HorarioDisponivel.__table__)).mappings().one()
    assert booking["id"] is not None
    assert booking["status"] == "pendente"
    assert booking["preco_solicitado"] == Decimal("125.50")
    assert booking["criado_em"].utcoffset() is not None
    assert service["ativo"] is True
    assert slot["bloqueado"] is False
    assert slot["inicio"] == seed["start"]


@pytest.mark.parametrize("field,value", [
    ("preco", 0), ("preco", -1), ("preco", Decimal("NaN")),
    ("duracao_minutos", 0), ("duracao_minutos", -1), ("nome", " "),
])
def test_check_servico_rejeita_valores_invalidos(db, seed, field, value):
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(update(Servico).where(Servico.id == seed["service"]).values(**{field: value}))
    assert error.value.orig.sqlstate == "23514"


def test_email_unico_e_fk_restritiva(db, seed):
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(insert(Administrador).values(
            nome="Duplicada", email="admin@example.test", senha_hash="hash_de_teste",
        ))
    assert error.value.orig.sqlstate == "23505"
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(delete(Administrador).where(Administrador.id == seed["admin"]))
    assert error.value.orig.sqlstate == "23503"


def test_agendamento_rejeita_fk_inexistente(db, seed):
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(insert(Agendamento).values(**booking_values(seed, servico_id=uuid4())))
    assert error.value.orig.sqlstate == "23503"


@pytest.mark.parametrize("field,value", [
    ("status", "confirmado"), ("cliente_nome", " "), ("cliente_telefone", ""),
    ("preco_solicitado", 0), ("duracao_minutos_solicitada", 0),
    ("duracao_minutos_solicitada", 121),
])
def test_check_agendamento_rejeita_valores_invalidos(db, seed, field, value):
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(insert(Agendamento).values(**booking_values(seed, **{field: value})))
    assert error.value.orig.sqlstate == "23514"


def test_intervalo_invalido_e_sobreposicao_rejeitados(db, seed):
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(insert(HorarioDisponivel).values(
            administrador_id=seed["admin"], inicio=seed["start"], fim=seed["start"],
        ))
    assert error.value.orig.sqlstate == "23514"
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(insert(HorarioDisponivel).values(
            administrador_id=seed["admin"], inicio=seed["start"] + timedelta(hours=1),
            fim=seed["start"] + timedelta(hours=3),
        ))
    assert error.value.orig.sqlstate == "23P01"
    with db.begin() as connection:
        connection.execute(insert(HorarioDisponivel).values(
            administrador_id=seed["admin"], inicio=seed["start"] + timedelta(hours=2),
            fim=seed["start"] + timedelta(hours=3),
        ))


@pytest.mark.parametrize("released_status", ["recusado", "cancelado"])
def test_liberacao_do_indice_preserva_historico_e_bloqueio(db, seed, released_status):
    with db.begin() as connection:
        booking = connection.execute(insert(Agendamento).values(**booking_values(seed))
                                     .returning(Agendamento.id)).scalar_one()
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(insert(Agendamento).values(**booking_values(seed, status="aprovado")))
    assert error.value.orig.sqlstate == "23505"
    with db.begin() as connection:
        connection.execute(update(HorarioDisponivel).values(bloqueado=True))
        connection.execute(update(Agendamento).where(Agendamento.id == booking).values(status=released_status))
        assert connection.execute(select(HorarioDisponivel.bloqueado)).scalar_one() is True
        assert connection.execute(select(Agendamento.status)).scalar_one() == released_status
        connection.execute(update(HorarioDisponivel).values(bloqueado=False))
        connection.execute(insert(Agendamento).values(**booking_values(seed)))
        statuses = connection.execute(select(Agendamento.status)).scalars().all()
        assert sorted(statuses) == sorted([released_status, "pendente"])


@pytest.mark.parametrize("field,value", [("preco_solicitado", 200), ("duracao_minutos_solicitada", 90)])
def test_historico_permanece_apos_edicao_e_desativacao_do_servico(db, seed, field, value):
    with db.begin() as connection:
        connection.execute(insert(Agendamento).values(**booking_values(seed)))
        connection.execute(update(Servico).values(preco=200, duracao_minutos=90, ativo=False))
        booking = connection.execute(select(Agendamento.__table__)).mappings().one()
    assert booking["preco_solicitado"] == Decimal("125.50")
    assert booking["duracao_minutos_solicitada"] == 60
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(update(Agendamento).values(**{field: value}))
    assert error.value.orig.sqlstate == "23514"
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(delete(Servico))
    assert error.value.orig.sqlstate == "23503"


def test_reducao_de_bloco_nao_invalida_duracao_da_reserva(db, seed):
    with db.begin() as connection:
        connection.execute(insert(Agendamento).values(**booking_values(seed)))
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(update(HorarioDisponivel).values(fim=seed["start"] + timedelta(minutes=59)))
    assert error.value.orig.sqlstate == "23514"


def test_servico_e_horario_devem_ser_da_mesma_administradora(db, seed):
    with db.begin() as connection:
        other = connection.execute(insert(Administrador).values(
            nome="Outra fixture", email="outra@example.test", senha_hash="hash_de_teste",
        ).returning(Administrador.id)).scalar_one()
        slot = connection.execute(insert(HorarioDisponivel).values(
            administrador_id=other, inicio=seed["start"], fim=seed["start"] + timedelta(hours=2),
        ).returning(HorarioDisponivel.id)).scalar_one()
    with pytest.raises(IntegrityError) as error, db.begin() as connection:
        connection.execute(insert(Agendamento).values(**booking_values(seed, horario_id=slot)))
    assert error.value.orig.sqlstate == "23514"


@pytest.mark.parametrize("operation", ["reserva", "sobreposicao"])
def test_concorrencia_real_aceita_apenas_uma_transacao(db, seed, operation):
    barrier = Barrier(2)

    def attempt():
        try:
            with db.begin() as connection:
                barrier.wait(timeout=10)
                if operation == "reserva":
                    connection.execute(insert(Agendamento).values(**booking_values(seed)))
                else:
                    connection.execute(insert(HorarioDisponivel).values(
                        administrador_id=seed["admin"],
                        inicio=seed["start"] + timedelta(hours=3),
                        fim=seed["start"] + timedelta(hours=4),
                    ))
            return "aceita"
        except DBAPIError as error:
            return error.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: attempt(), range(2)))
    assert results.count("aceita") == 1
    assert set(results) <= {"aceita", "23505", "23P01", "40P01"}


def test_rls_e_privilegios_bloqueiam_acesso_direto(db, seed):
    tables = ("administradores", "servicos", "horarios_disponiveis", "agendamentos")
    with db.connect() as connection:
        for table in tables:
            assert connection.execute(text(
                "SELECT relrowsecurity FROM pg_class WHERE oid=CAST(:table AS regclass)"
            ), {"table": f"public.{table}"}).scalar_one() is True
            for role in ("anon", "authenticated", "service_role"):
                assert connection.execute(text(
                    "SELECT has_table_privilege(:role, :table, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE')"
                ), {"role": role, "table": f"public.{table}"}).scalar_one() is False
    with pytest.raises(DBAPIError) as error, db.begin() as connection:
        connection.execute(text("SET LOCAL ROLE anon"))
        connection.execute(text("SELECT * FROM public.administradores"))
    assert error.value.orig.sqlstate == "42501"


def test_reserva_concorrente_com_reducao_de_bloco_preserva_duracao(db, seed):
    barrier = Barrier(2)

    def attempt(operation):
        try:
            with db.begin() as connection:
                barrier.wait(timeout=10)
                if operation == "reserva":
                    connection.execute(insert(Agendamento).values(**booking_values(seed)))
                else:
                    connection.execute(update(HorarioDisponivel).where(
                        HorarioDisponivel.id == seed["slot"]
                    ).values(fim=seed["start"] + timedelta(minutes=30)))
            return "aceita"
        except DBAPIError as error:
            return error.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, ["reserva", "reducao"]))
    assert results.count("aceita") == 1
    assert set(results) <= {"aceita", "23514", "40P01"}
    with db.connect() as connection:
        assert connection.execute(text(
            "SELECT count(*) FROM agendamentos a JOIN horarios_disponiveis h "
            "ON h.id=a.horario_id WHERE a.status IN ('pendente','aprovado') "
            "AND a.duracao_minutos_solicitada * interval '1 minute' > h.fim-h.inicio"
        )).scalar_one() == 0


def test_metadata_e_migracao_sem_divergencia(db):
    with db.begin() as connection:
        connection.execute(text("CREATE TABLE public.objeto_externo_de_teste (id integer)"))
        try:
            command.check(migration_config(connection))
            assert connection.execute(text(
                "SELECT to_regclass('public.objeto_externo_de_teste')"
            )).scalar_one() is not None
        finally:
            connection.execute(text("DROP TABLE public.objeto_externo_de_teste"))


def test_downgrade_e_upgrade_somente_no_cluster_temporario(db):
    assert db.url.host == "127.0.0.1" and db.url.database == "mvp_integracao"
    with db.begin() as connection:
        config = migration_config(connection)
        command.downgrade(config, "base")
        assert connection.execute(text("SELECT to_regclass('public.agendamentos')")).scalar_one() is None
        command.upgrade(config, "head")
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0001_modelo_inicial"
