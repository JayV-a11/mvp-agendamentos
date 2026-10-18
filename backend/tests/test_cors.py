import pytest


def test_origem_do_frontend_permitida(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4200"
    assert "access-control-allow-credentials" not in response.headers


@pytest.mark.parametrize(
    "origin, method",
    [
        ("https://origem-nao-permitida.example", "GET"),
        ("http://localhost:4200", "POST"),
    ],
)
def test_preflight_nao_permitido(client, origin, method):
    response = client.options(
        "/health",
        headers={"Origin": origin, "Access-Control-Request-Method": method},
    )

    assert response.status_code == 400


def test_origem_desconhecida_nao_recebe_permissao_cors(client):
    response = client.get(
        "/health", headers={"Origin": "https://origem-nao-permitida.example"}
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
