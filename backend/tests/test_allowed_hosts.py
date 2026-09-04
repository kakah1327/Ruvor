"""F3-10: RUVOR_ALLOWED_HOSTS tolera espaco em volta da virgula."""

from config.settings import _split_hosts


def test_espaco_em_volta_da_virgula_e_removido() -> None:
    assert _split_hosts("localhost, 127.0.0.1") == ["localhost", "127.0.0.1"]


def test_string_vazia_vira_lista_vazia() -> None:
    assert _split_hosts("") == []


def test_item_vazio_e_descartado() -> None:
    assert _split_hosts("a,,b") == ["a", "b"]


def test_um_host_com_espaco_nas_duas_pontas() -> None:
    assert _split_hosts("  web  ") == ["web"]


def test_item_so_de_espaco_e_descartado() -> None:
    assert _split_hosts("a, ,b") == ["a", "b"]
