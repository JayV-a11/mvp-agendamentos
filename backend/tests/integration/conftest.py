import os
import secrets
import shlex
import socket
import subprocess
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import URL, create_engine, text
from sqlalchemy.pool import NullPool


@pytest.fixture(scope="session")
def postgres_cluster(request, tmp_path_factory):
    binary_directory = request.config.getoption("--postgres-bin")
    if not binary_directory:
        pytest.skip("Integração PostgreSQL exige --postgres-bin; nenhum banco externo será usado.")

    binary_directory = Path(binary_directory).resolve()
    suffix = ".exe" if os.name == "nt" else ""
    initdb = binary_directory / f"initdb{suffix}"
    pg_ctl = binary_directory / f"pg_ctl{suffix}"
    if not initdb.is_file() or not pg_ctl.is_file():
        pytest.fail("--postgres-bin deve conter initdb e pg_ctl.")

    directory = tmp_path_factory.mktemp("postgres_isolado")
    data = directory / "data"
    password = secrets.token_urlsafe(24)
    password_file = directory / "senha_inicial"
    password_file.write_text(password, encoding="utf-8")
    env = os.environ.copy()
    env["PATH"] = str(binary_directory) + os.pathsep + env.get("PATH", "")
    env["LC_MESSAGES"] = "C"

    def run(*args):
        # Um servidor iniciado por pg_ctl pode herdar pipes no Windows. Use arquivo
        # para não manter communicate() esperando pelo processo em segundo plano.
        command_log = directory / "commands.log"
        with command_log.open("a", encoding="utf-8") as output:
            result = subprocess.run(
                [str(arg) for arg in args], stdout=output, stderr=subprocess.STDOUT,
                timeout=60, env=env,
            )
        if result.returncode:
            raise RuntimeError(
                "Comando PostgreSQL local falhou: "
                + command_log.read_text(encoding="utf-8", errors="replace")
            )

    run(initdb, "-D", data, "-U", "postgres", "--encoding=UTF8", "--no-locale",
        "--auth=scram-sha-256", f"--pwfile={password_file}")
    password_file.unlink()
    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]
    try:
        server_options = ["-h", "127.0.0.1", "-p", str(port)]
        if os.name != "nt":
            # O runner Linux não pode gravar no diretório de sockets do serviço
            # PostgreSQL do sistema. O socket pertence ao cluster descartável.
            server_options.extend(["-k", str(directory)])
        options = (subprocess.list2cmdline(server_options) if os.name == "nt"
                   else shlex.join(server_options))
        run(pg_ctl, "-D", data, "-l", directory / "server.log", "-w", "-t", "30",
            "-o", options, "start")
        yield URL.create(
            "postgresql+psycopg", username="postgres", password=password,
            host="127.0.0.1", port=port, database="postgres",
        )
    finally:
        if (data / "postmaster.pid").exists():
            run(pg_ctl, "-D", data, "-w", "-t", "30", "-m", "fast", "stop")


@pytest.fixture(scope="session")
def database_engine(postgres_cluster):
    # Este engine não lê DATABASE_URL nem usa Supabase. O cluster foi criado acima.
    options = {"poolclass": NullPool, "connect_args": {"sslmode": "disable"}, "hide_parameters": True}
    bootstrap = create_engine(postgres_cluster, **options)
    with bootstrap.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text("CREATE DATABASE mvp_integracao"))
        for role in ("anon", "authenticated", "service_role"):
            connection.execute(text(f'CREATE ROLE "{role}" NOLOGIN'))
    bootstrap.dispose()
    engine = create_engine(postgres_cluster.set(database="mvp_integracao"), **options)
    with engine.begin() as connection:
        # Reproduz grants que não podem expor as tabelas criadas por migrações.
        connection.execute(text(
            "ALTER DEFAULT PRIVILEGES GRANT ALL ON TABLES TO anon, authenticated, service_role"
        ))
        config = migration_config(connection)
        command.upgrade(config, "head")
    try:
        yield engine
    finally:
        engine.dispose()


def migration_config(connection):
    backend = Path(__file__).resolve().parents[2]
    config = Config(str(backend / "alembic.ini"))
    config.attributes["connection"] = connection
    return config


@pytest.fixture
def db(database_engine):
    assert database_engine.url.host == "127.0.0.1"
    assert database_engine.url.database == "mvp_integracao"
    yield database_engine
    with database_engine.begin() as connection:
        connection.execute(text(
            "TRUNCATE public.limites_requisicoes, public.agendamentos, public.horarios_disponiveis, "
            "public.servicos, public.administradores CASCADE"
        ))
