"""Tests for transparencia-sp-fetcher catalog (sem rede)."""

from __future__ import annotations

import pytest

from transparencia_sp_fetcher.catalog import GROUP_ALIASES, GROUPS, list_datasets


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
