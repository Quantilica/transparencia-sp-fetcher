"""Tests for TransparenciaSpClient."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from quantilica.core.manifests import DownloadManifest

from transparencia_sp_fetcher.client import TransparenciaSpClient


def test_client_init() -> None:
    client = TransparenciaSpClient()
    assert client.client is not None
    assert client.base_url == "https://www.transparencia.sp.gov.br"


def test_download_corrente(tmp_path) -> None:
    client = TransparenciaSpClient()
    target = tmp_path / "remuneracao_corrente.csv"
    mock_manifest = MagicMock(spec=DownloadManifest)
    with patch.object(
        client.client, "download_with_manifest", return_value=mock_manifest
    ):
        res = client.download_corrente(target)
        assert res == mock_manifest


def test_download_historico(tmp_path) -> None:
    client = TransparenciaSpClient()
    target = tmp_path / "remuneracao_2026_08.zip"
    mock_manifest = MagicMock(spec=DownloadManifest)
    with patch.object(
        client.client, "download_with_manifest", return_value=mock_manifest
    ) as mock_dl:
        res = client.download_historico("71", target)
        assert res == mock_manifest
        assert "id=71&f=zip" in mock_dl.call_args[0][0]


def test_download_dicionario(tmp_path) -> None:
    client = TransparenciaSpClient()
    target = tmp_path / "dicionario.pdf"
    mock_manifest = MagicMock(spec=DownloadManifest)
    with patch.object(
        client.client, "download_with_manifest", return_value=mock_manifest
    ):
        res = client.download_dicionario(target)
        assert res == mock_manifest
