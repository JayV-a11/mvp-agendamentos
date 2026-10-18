from pathlib import Path
from shutil import copyfile

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_template_gera_revisao_importavel_em_diretorio_isolado(tmp_path):
    template = Path(__file__).resolve().parents[1] / "alembic" / "script.py.mako"
    copyfile(template, tmp_path / "script.py.mako")
    (tmp_path / "versions").mkdir()
    config = Config()
    config.set_main_option("script_location", str(tmp_path))
    config.set_main_option("path_separator", "os")

    revision = ScriptDirectory.from_config(config).generate_revision(
        "teste_infra", "verifica template sem conexão", head="base"
    )

    assert revision is not None
    assert revision.module.revision == "teste_infra"
    assert revision.module.down_revision is None
    assert callable(revision.module.upgrade)
    assert callable(revision.module.downgrade)
