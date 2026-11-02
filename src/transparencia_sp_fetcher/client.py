"""HTTP client for Portal da Transparência SP."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from quantilica.core.http import HttpClient
from quantilica.core.logging import get_logger
from quantilica.core.manifests import DownloadManifest

from .constants import (
    DICIONARIO_URL,
    DOWNLOAD_CORRENTE_URL,
    DOWNLOAD_HISTORICO_URL,
    REMUNERACAO_PAGE_URL,
    TRANSPARENCIA_SP_BASE_URL,
)

logger = get_logger(__name__)

_MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

_HISTORICO_ROW_RE = re.compile(
    r"<strong>\s*(\d{4})\s*-\s*([^<]+?)\s*</strong>.*?downloadhistorico\?id=(\d+)",
    re.DOTALL,
)


class TransparenciaSpClient:
    """Client for downloading payroll files from SP Transparency Portal."""

    def __init__(
        self,
        *,
        base_url: str = TRANSPARENCIA_SP_BASE_URL,
        client: HttpClient | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or HttpClient()
        self.logger = logger or get_logger(__name__)

    def download_corrente(
        self,
        dest: Path,
        *,
        manifest_path: Path | None = None,
    ) -> DownloadManifest:
        """Download latest payroll consolidated CSV."""
        return self.client.download_with_manifest(
            DOWNLOAD_CORRENTE_URL,
            dest,
            manifest_path=manifest_path,
        )

    def list_historico(self) -> list[dict[str, Any]]:
        """Descobre os arquivos históricos reais na página de remuneração.

        O endpoint ``downloadhistorico`` não aceita ``ano``/``mes``: cada mês
        tem um ``id`` numérico publicado na tabela da página. A descoberta lê
        essa tabela para não depender de ids fixos.

        Returns:
            Lista de dicts com ``id``, ``ano``, ``mes``, ``label`` e ``url``.
        """
        response = self.client.get(REMUNERACAO_PAGE_URL)
        response.raise_for_status()
        arquivos: list[dict[str, Any]] = []
        for ano, mes_nome, file_id in _HISTORICO_ROW_RE.findall(response.text):
            mes = _MESES.get(mes_nome.strip().lower())
            if mes is None:
                continue
            item = {
                "id": file_id,
                "ano": int(ano),
                "mes": mes,
                "label": f"{ano}-{mes:02d}",
                "url": f"{DOWNLOAD_HISTORICO_URL}?id={file_id}&f=zip",
            }
            # A página lista meses cujo arquivo ainda não foi publicado (404)
            # ou está bloqueado temporariamente (405). Sondar só os headers
            # evita transformar isso em erro de download no cron.
            try:
                probe = self.client.head_or_get(item["url"])
            except Exception:  # noqa: BLE001 - indisponível hoje, volta amanhã
                continue
            if probe.status_code in (200, 206):
                arquivos.append(item)
        return sorted(arquivos, key=lambda a: (a["ano"], a["mes"]))

    def download_historico(
        self,
        file_id: str,
        dest: Path,
        *,
        manifest_path: Path | None = None,
    ) -> DownloadManifest:
        """Download monthly historical payroll archive by its published id."""
        url = f"{DOWNLOAD_HISTORICO_URL}?id={file_id}&f=zip"
        return self.client.download_with_manifest(
            url,
            dest,
            manifest_path=manifest_path,
        )

    def download_dicionario(
        self,
        dest: Path,
        *,
        manifest_path: Path | None = None,
    ) -> DownloadManifest:
        """Download data dictionary."""
        return self.client.download_with_manifest(
            DICIONARIO_URL,
            dest,
            manifest_path=manifest_path,
        )
