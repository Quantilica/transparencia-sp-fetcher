"""Dataset catalog for transparencia-sp-fetcher.

A série histórica não é endereçável por ``ano``/``mes``: cada mês tem um
``id`` numérico publicado na página de remuneração. O grupo ``historico`` é
portanto descoberto a partir da tabela real; ``corrente`` e ``dicionario`` são
estáticos.
"""

from __future__ import annotations

from typing import Any

from ._catalog_base import DatasetEntry, GroupInfo, static_dataset
from .client import TransparenciaSpClient
from .constants import (
    DICIONARIO_URL,
    DOWNLOAD_CORRENTE_URL,
    RAR_END,
    RAR_START,
    rar_url,
)

__all__ = [
    "DatasetEntry",
    "GroupInfo",
    "GROUPS",
    "GROUP_ALIASES",
    "list_datasets",
]

_HISTORICO_CACHE: list[dict[str, Any]] | None = None

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
        entries=[],
    ).to_dict(),
    "rar": GroupInfo(
        name="Remuneração dos Servidores SP — Série Antiga (RAR, jun/2012–mar/2023)",
        entries=[],
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
    "serie": "historico",
    "historico_mensal": "historico",
    "serie_antiga": "rar",
    "historico_rar": "rar",
}


def _rar_entries() -> list[dict[str, Any]]:
    """Série antiga (RAR): 130 meses por aritmética; o servidor não a lista.

    Não há listagem nem HEAD (405, Range ignorado): a existência de cada mês foi
    conferida na varredura de 27/10/2026 e o ``check`` do SDK sonda por GET de
    cabeçalhos.
    """
    entries: list[dict[str, Any]] = []
    ano, mes = RAR_START
    while (ano, mes) <= RAR_END:
        entries.append(
            DatasetEntry(
                id=f"remuneracao_rar_{ano}_{mes:02d}",
                base_id="remuneracao_rar",
                name=f"Remuneração dos Servidores SP — série antiga ({ano}-{mes:02d})",
                url=rar_url(ano, mes),
                ext="rar",
                group="rar",
                year=ano,
                month=mes,
            ).to_dict()
        )
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    return entries


def _historico_entries() -> list[dict[str, Any]]:
    """Descobre a série histórica real (cache por processo)."""
    global _HISTORICO_CACHE
    if _HISTORICO_CACHE is None:
        _HISTORICO_CACHE = [
            DatasetEntry(
                id=f"remuneracao_{item['label'].replace('-', '_')}",
                base_id="remuneracao",
                name=f"Remuneração dos Servidores SP ({item['label']})",
                url=item["url"],
                ext="zip",
                group="historico",
                year=item["ano"],
                month=item["mes"],
            ).to_dict()
            for item in TransparenciaSpClient().list_historico()
        ]
    return _HISTORICO_CACHE


def list_datasets(group: str | None = None) -> list[dict[str, Any]]:
    """Lista datasets for a group or all groups."""
    if group is None:
        entries: list[dict[str, Any]] = []
        entries.extend(GROUPS["corrente"]["entries"])
        entries.extend(_rar_entries())
        entries.extend(_historico_entries())
        entries.extend(GROUPS["dicionario"]["entries"])
        return entries

    canon = GROUP_ALIASES.get(group, group)
    if canon not in GROUPS:
        raise ValueError(f"Grupo desconhecido: {group!r}")
    if canon == "rar":
        return _rar_entries()
    if canon == "historico":
        return list(_historico_entries())
    return list(GROUPS[canon]["entries"])
