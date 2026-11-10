"""O plugin declara o FetcherInfo do registro de fetchers."""

from transparencia_sp_fetcher.plugin import fetcher


def test_info_declarado():
    app = fetcher
    assert app.info_declared is True
    assert app.info.id == "transparencia-sp"
    assert app.info.orgao
