"""HTTP client for Portal da Transparência SP."""

from __future__ import annotations

import logging
from pathlib import Path

from quantilica.core.http import HttpClient
from quantilica.core.logging import get_logger
from quantilica.core.manifests import DownloadManifest

from .constants import (
    DICIONARIO_URL,
    DOWNLOAD_CORRENTE_URL,
    DOWNLOAD_HISTORICO_URL,
    TRANSPARENCIA_SP_BASE_URL,
)

logger = get_logger(__name__)


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

    def download_historico(
        self,
        ano: int,
        mes: int,
        dest: Path,
        *,
        manifest_path: Path | None = None,
    ) -> DownloadManifest:
        """Download monthly historical payroll archive."""
        url = f"{DOWNLOAD_HISTORICO_URL}?ano={ano}&mes={mes}"
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
