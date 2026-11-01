"""Dataset catalog for transparencia-sp-fetcher."""

from __future__ import annotations

import datetime as dt
from typing import Any

from ._catalog_base import DatasetEntry, GroupInfo, monthly_datasets, static_dataset
from .constants import (
    DICIONARIO_URL,
    DOWNLOAD_CORRENTE_URL,
    DOWNLOAD_HISTORICO_URL,
    START_YEAR,
)

__all__ = [
    "DatasetEntry",
    "GroupInfo",
    "GROUPS",
    "GROUP_ALIASES",
    "list_datasets",
]

_current_year = dt.date.today().year

GROUPS: dict[str, dict[str, Any]] = {
    "corrente": GroupInfo(
        name="Remuneração dos Servidores Públicos de SP (Mês Corrente)",
        entries=[
            static_dataset(
                "corrente",
                id="remuneracao_corrente",
                name="Remuneração dos Servidores SP - Arquivo Consolidado Corrente",
                url=DOWNLOAD_CORRENTE_URL,
                ext="csv",
            )
        ],
    ).to_dict(),
    "historico": GroupInfo(
        name="Remuneração dos Servidores SP — Série Histórica Mensal",
        entries=monthly_datasets(
            "historico",
            base_id="remuneracao",
            name_template="Remuneração dos Servidores SP ({year}-{month:02d})",
            url_template=f"{DOWNLOAD_HISTORICO_URL}?ano={{year}}&mes={{month}}",
            start_year=START_YEAR,
            end_year=_current_year,
            ext="zip",
        ),
    ).to_dict(),
    "dicionario": GroupInfo(
        name="Dicionário de Dados de Remuneração",
        entries=[
            static_dataset(
                "dicionario",
                id="dicionario_remuneracao",
                name="Dicionário de Dados - Remuneração SP",
                url=DICIONARIO_URL,
                ext="xlsx",
            )
        ],
    ).to_dict(),
}

GROUP_ALIASES: dict[str, str] = {
    "padrao": "corrente",
    "remuneracao": "corrente",
    "sp_remuneracao": "corrente",
    "servidores": "corrente",
    "folha": "corrente",
}


def list_datasets(group: str | None = None) -> list[dict[str, Any]]:
    """List datasets for a group or all groups."""
    if group is None:
        entries: list[dict[str, Any]] = []
        for g_data in GROUPS.values():
            entries.extend(g_data["entries"])
        return entries

    canon = GROUP_ALIASES.get(group, group)
    if canon not in GROUPS:
        raise ValueError(f"Grupo desconhecido: {group!r}")
    return list(GROUPS[canon]["entries"])
