"""Pytest configuration and fixtures for transparencia-sp-fetcher."""

from __future__ import annotations

import pytest

from transparencia_sp_fetcher import catalog

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
