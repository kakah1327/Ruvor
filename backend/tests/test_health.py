from django.test import Client


def test_health_responde_ok(client: Client) -> None:
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
