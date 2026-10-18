def test_health_responde_sem_autenticacao(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"] == "application/json"


def test_openapi_documenta_fluxos_publicos_e_administrativos(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()['paths']
    assert {'/health', '/auth/login', '/auth/sessao', '/auth/logout',
        '/admin/servicos', '/admin/horarios', '/admin/agendamentos',
        '/publico/servicos', '/publico/agendamentos'} <= set(paths)
