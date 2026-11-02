"""Tests for transparencia-sp-fetcher catalog (sem rede)."""

from __future__ import annotations

import pytest

from transparencia_sp_fetcher import catalog
from transparencia_sp_fetcher.catalog import GROUP_ALIASES, GROUPS, list_datasets

FAKE_HISTORICO = [
    {
        "id": "70",
        "ano": 2026,
        "mes": 7,
        "label": "2026-07",
        "url": "https://x/Remuneracao/downloadhistorico?id=70&f=zip",
    },
    {
        "id": "71",
        "ano": 2026,
        "mes": 8,
        "label": "2026-08",
        "url": "https://x/Remuneracao/downloadhistorico?id=71&f=zip",
    },
]


@pytest.fixture(autouse=True)
def fake_historico(monkeypatch: pytest.MonkeyPatch) -> None:
    """Substitui a descoberta da página por uma série fixa."""
    monkeypatch.setattr(catalog, "_HISTORICO_CACHE", None)
    monkeypatch.setattr(
        catalog.TransparenciaSpClient,
        "list_historico",
        lambda self: list(FAKE_HISTORICO),
    )


def test_historico_usa_ids_descobertos() -> None:
    """Cada mês vira uma entrada com o id real na URL."""
    entries = list_datasets("historico")
    assert [e["id"] for e in entries] == [
        "remuneracao_2026_07",
        "remuneracao_2026_08",
    ]
    assert entries[1]["url"].endswith("id=71&f=zip")
    assert entries[1]["month"] == 8


def test_list_datasets_all_inclui_os_tres_grupos() -> None:
    ids = {e["id"] for e in list_datasets()}
    assert {"remuneracao_corrente", "dicionario_remuneracao"} <= ids
    assert "remuneracao_2026_08" in ids


def test_list_datasets_por_grupo_e_alias() -> None:
    """Grupos e aliases válidos respondem; inválido levanta ValueError."""
    for group in GROUPS:
        assert isinstance(list_datasets(group), list)
    for alias in GROUP_ALIASES:
        assert isinstance(list_datasets(alias), list)
    with pytest.raises(ValueError, match="Grupo desconhecido"):
        list_datasets("grupo_inexistente_xyz")
