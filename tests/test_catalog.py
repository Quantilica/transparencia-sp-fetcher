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


def test_serie_antiga_rar_jun2012_a_mar2023() -> None:
    """130 meses; março usa ``Março`` até 2016 e ``Marco`` de 2017 em diante."""
    entries = list_datasets("rar")
    assert len(entries) == 130
    assert (entries[0]["year"], entries[0]["month"]) == (2012, 6)
    assert (entries[-1]["year"], entries[-1]["month"]) == (2023, 3)
    assert len({e["id"] for e in entries}) == 130
    urls = {e["id"]: e["url"] for e in entries}
    base = "https://www.transparencia.sp.gov.br/PortalTransparencia-Report/historico"
    assert urls["remuneracao_rar_2012_06"] == f"{base}/remuneracao_Junho_2012.rar"
    assert urls["remuneracao_rar_2016_03"] == f"{base}/remuneracao_Mar%C3%A7o_2016.rar"
    assert urls["remuneracao_rar_2017_03"] == f"{base}/remuneracao_Marco_2017.rar"
    assert all(e["ext"] == "rar" and e["group"] == "rar" for e in entries)


def test_rar_entra_no_catalogo_completo() -> None:
    assert "remuneracao_rar_2020_01" in {e["id"] for e in list_datasets()}
    assert list_datasets("serie_antiga") == list_datasets("rar")
