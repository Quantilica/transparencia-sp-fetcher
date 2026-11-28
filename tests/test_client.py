"""Testes da descoberta do histórico (sem rede: transporte simulado)."""

from __future__ import annotations

import logging
import sys

import httpx2
import pytest
from quantilica.core.http import HttpClient

from transparencia_sp_fetcher import catalog
from transparencia_sp_fetcher.client import (
    SONDAGEM_ATTEMPTS,
    SONDAGEM_HEADERS,
    SONDAGEM_POLICY,
    SONDAGEM_TIMEOUT,
    DiscoveryError,
    TransparenciaSpClient,
    parse_historico_page,
)

PAGE_PATH = "/Remuneracao"
_LIST_HISTORICO_REAL = TransparenciaSpClient.list_historico


@pytest.fixture(autouse=True)
def descoberta_real(fake_historico: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Desfaz a série fixa do ``conftest``: aqui a descoberta roda de verdade."""
    monkeypatch.setattr(TransparenciaSpClient, "list_historico", _LIST_HISTORICO_REAL)


def _linha(ano: int, mes: str, file_id: str | None) -> str:
    link = (
        f'<a class="btn" href="/Remuneracao/downloadhistorico?id={file_id}&amp;f=zip">'
        "Baixar</a>"
        if file_id
        else "<span>Indisponível</span>"
    )
    return (
        f'<tr><td><strong>{ano} - {mes}</strong></td><td class="acao">{link}</td></tr>'
    )


def _pagina(*linhas: str) -> str:
    return (
        "<html><body><div id='historico'><table class='table'>"
        "<thead><tr><th>Período</th><th>Arquivo</th></tr></thead><tbody>"
        + "".join(linhas)
        + "</tbody></table></div></body></html>"
    )


def _cliente(handler, *, attempts: int = 1) -> TransparenciaSpClient:
    http = HttpClient(
        transport=httpx2.MockTransport(handler),
        attempts=attempts,
        retry_base_delay=0.0,
        jitter=0.0,
    )
    return TransparenciaSpClient(client=http)


def _servidor(pagina: str | int, arquivos: dict[str, tuple[int, str]]):
    """Handler: ``pagina`` é o HTML (200) ou o status; ``arquivos`` id -> resposta."""
    pedidos: list[tuple[str, str]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        pedidos.append((request.method, str(request.url)))
        if request.url.path == PAGE_PATH:
            if isinstance(pagina, int):
                return httpx2.Response(pagina, text="erro")
            return httpx2.Response(
                200, text=pagina, headers={"content-type": "text/html"}
            )
        status, tipo = arquivos[request.url.params["id"]]
        return httpx2.Response(status, headers={"content-type": tipo})

    handler.pedidos = pedidos  # type: ignore[attr-defined]
    return handler


ZIP = "application/zip"
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto"]


# --- parser ---------------------------------------------------------------


def test_mes_sem_link_nao_herda_o_id_da_linha_seguinte() -> None:
    """Caso sintético da auditoria: setembro sem link ficava com o id de outubro."""
    html = _pagina(
        _linha(2026, "Agosto", "71"),
        _linha(2026, "Setembro", None),
        _linha(2026, "Outubro", "73"),
    )
    linhas, orfaos = parse_historico_page(html)
    por_mes = {(ln.ano, ln.mes_nome): ln.file_id for ln in linhas}
    assert por_mes == {
        (2026, "Agosto"): "71",
        (2026, "Setembro"): None,
        (2026, "Outubro"): "73",
    }
    assert orfaos == 0


def test_mes_sem_link_no_fim_da_tabela_e_sem_tr_fechado() -> None:
    """``<tr>`` sem fechamento (HTML válido) também delimita a linha."""
    html = (
        "<table>"
        "<tr><td><strong>2026 - Julho</strong><td>"
        '<a href="/Remuneracao/downloadhistorico?id=70&f=zip">z</a>'
        "<tr><td><strong>2026 - Agosto</strong><td>—"
    )
    linhas, _ = parse_historico_page(html)
    assert [(ln.mes_nome, ln.file_id) for ln in linhas] == [
        ("Julho", "70"),
        ("Agosto", None),
    ]


def test_marcacao_sem_tr_novo_rotulo_abre_nova_linha() -> None:
    html = (
        '<div><strong>2026 - Julho</strong> <a href="downloadhistorico?id=70">z</a>'
        "</div>"
        "<div><strong>2026 - Agosto</strong></div>"
        '<div><strong>2026 - Setembro</strong> <a href="downloadhistorico?id=72">z</a>'
        "</div>"
    )
    linhas, _ = parse_historico_page(html)
    assert [(ln.mes_nome, ln.file_id) for ln in linhas] == [
        ("Julho", "70"),
        ("Agosto", None),
        ("Setembro", "72"),
    ]


def test_recorte_realista_da_pagina() -> None:
    """Tabela com cabeçalho, rótulos com espaços e entidades, link com ``&amp;``."""
    html = """
    <div class="tab-pane" id="historico">
      <table class="table table-striped">
        <thead><tr><th>Mês de referência</th><th>Download</th></tr></thead>
        <tbody>
          <tr>
            <td>
              <strong> 2026 -&nbsp;Agosto </strong>
            </td>
            <td class="text-right">
              <a href="/Remuneracao/downloadhistorico?id=71&amp;f=zip" title="ZIP">
                <i class="fa fa-download"></i> Baixar
              </a>
            </td>
          </tr>
          <tr>
            <td><strong>2026 - Maio</strong></td>
            <td><a href="/Remuneracao/downloadhistorico?id=68&amp;f=zip">Baixar</a></td>
          </tr>
          <tr>
            <td><strong>2023 - Março</strong></td>
            <td><a href="/Remuneracao/downloadhistorico?id=30&amp;f=zip">Baixar</a></td>
          </tr>
        </tbody>
      </table>
      <a href="/Remuneracao/Download?arquivo=Remuneracao.csv">Mês corrente</a>
    </div>
    """
    linhas, orfaos = parse_historico_page(html)
    assert [(ln.ano, ln.mes_nome, ln.file_id) for ln in linhas] == [
        (2026, "Agosto", "71"),
        (2026, "Maio", "68"),
        (2023, "Março", "30"),
    ]
    assert orfaos == 0


def test_link_sem_rotulo_e_contado() -> None:
    html = _pagina(
        _linha(2026, "Agosto", "71"),
        '<tr><td>sem mês</td><td><a href="/Remuneracao/downloadhistorico?id=99">x</a>'
        "</td></tr>",
    )
    linhas, orfaos = parse_historico_page(html)
    assert [ln.file_id for ln in linhas] == ["71"]
    assert orfaos == 1


# --- list_historico -------------------------------------------------------


def test_list_historico_so_exclui_404_e_mantem_falhas_no_catalogo(
    caplog: pytest.LogCaptureFixture,
) -> None:
    pagina = _pagina(
        _linha(2026, "Agosto", "71"),  # 200 zip
        _linha(2026, "Setembro", "72"),  # 404: ainda não publicado
        _linha(2026, "Outubro", "73"),  # 403 (firewall)
        _linha(2026, "Novembro", "74"),  # 429
        _linha(2026, "Dezembro", "75"),  # 500
        _linha(2027, "Janeiro", "76"),  # 200 mas HTML no lugar do arquivo
        _linha(2027, "Fevereiro", None),  # sem link
        _linha(2027, "Março", "77"),  # 206
    )
    handler = _servidor(
        pagina,
        {
            "71": (200, ZIP),
            "72": (404, "text/html"),
            "73": (403, "text/html"),
            "74": (429, "text/html"),
            "75": (500, "text/html"),
            "76": (200, "text/html; charset=utf-8"),
            "77": (206, ZIP),
        },
    )
    cliente = _cliente(handler)
    with caplog.at_level(logging.WARNING):
        itens = cliente.list_historico()

    assert [(i["label"], i["id"]) for i in itens] == [
        ("2026-08", "71"),
        ("2026-10", "73"),
        ("2026-11", "74"),
        ("2026-12", "75"),
        ("2027-01", "76"),
        ("2027-03", "77"),
    ]
    assert itens[0]["url"].endswith("downloadhistorico?id=71&f=zip")
    texto = caplog.text
    assert "2026-09" in texto and "404" in texto  # registrado, fora do catálogo
    assert "2027-02" in texto and "sem link" in texto
    for label in ("2026-10", "2026-11", "2026-12", "2027-01"):
        assert f"Histórico {label}: sondagem" in texto
    assert "com sondagem falha entram no catálogo" in texto


def test_list_historico_excecao_de_rede_entra_no_catalogo() -> None:
    pagina = _pagina(_linha(2026, "Agosto", "71"), _linha(2026, "Setembro", "72"))

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == PAGE_PATH:
            return httpx2.Response(200, text=pagina)
        if request.url.params["id"] == "72":
            raise httpx2.ConnectError("conexão recusada", request=request)
        return httpx2.Response(200, headers={"content-type": ZIP})

    itens = _cliente(handler).list_historico()
    assert [i["label"] for i in itens] == ["2026-08", "2026-09"]


def test_sondagem_para_apos_falhas_seguidas_e_nao_esvazia_a_serie() -> None:
    pagina = _pagina(*(_linha(2026, m, str(40 + i)) for i, m in enumerate(MESES)))
    handler = _servidor(pagina, {str(40 + i): (403, "text/html") for i in range(8)})
    itens = _cliente(handler).list_historico()
    assert len(itens) == 8
    # HEAD + GET de fallback (403) por mês sondado, 5 meses sondados.
    sondagens = [p for p in handler.pedidos if "downloadhistorico" in p[1]]
    assert len(sondagens) == 10


def test_404_no_meio_zera_a_contagem_de_falhas_seguidas() -> None:
    pagina = _pagina(*(_linha(2026, m, str(40 + i)) for i, m in enumerate(MESES)))
    arquivos = {str(40 + i): (500, "text/html") for i in range(8)}
    arquivos["43"] = (404, "text/html")
    handler = _servidor(pagina, arquivos)
    itens = _cliente(handler).list_historico()
    assert len(itens) == 7  # só o 404 fica de fora
    # 500 em HEAD não tem fallback: um pedido por mês, todos os 8 sondados.
    assert len([p for p in handler.pedidos if "downloadhistorico" in p[1]]) == 8


@pytest.mark.parametrize("status", [403, 429, 500, 503])
def test_pagina_inacessivel_e_erro_de_descoberta(status: int) -> None:
    with pytest.raises(DiscoveryError, match="ilegível"):
        _cliente(_servidor(status, {})).list_historico()


def test_pagina_sem_nenhuma_linha_reconhecivel_e_erro() -> None:
    pagina = "<html><body><h1>Em manutenção</h1><p>Volte logo.</p></body></html>"
    with pytest.raises(DiscoveryError, match="marcação mudou"):
        _cliente(_servidor(pagina, {})).list_historico()


def test_linhas_sem_nenhum_link_e_erro() -> None:
    pagina = _pagina(_linha(2026, "Agosto", None), _linha(2026, "Setembro", None))
    with pytest.raises(DiscoveryError, match="nenhuma com mês conhecido e link"):
        _cliente(_servidor(pagina, {})).list_historico()


def test_mes_desconhecido_e_ignorado_mas_o_resto_segue(
    caplog: pytest.LogCaptureFixture,
) -> None:
    pagina = _pagina(_linha(2026, "Agosto", "71"), _linha(2026, "Fooember", "99"))
    handler = _servidor(pagina, {"71": (200, ZIP)})
    with caplog.at_level(logging.WARNING):
        itens = _cliente(handler).list_historico()
    assert [i["label"] for i in itens] == ["2026-08"]
    assert "mês desconhecido" in caplog.text


def test_todos_os_meses_404_e_erro() -> None:
    pagina = _pagina(_linha(2026, "Agosto", "71"), _linha(2026, "Setembro", "72"))
    handler = _servidor(pagina, {"71": (404, "text/html"), "72": (404, "text/html")})
    with pytest.raises(DiscoveryError, match="deram 404 ou 405"):
        _cliente(handler).list_historico()


# --- cliente e catálogo ---------------------------------------------------


def test_cliente_padrao_respeita_ssl_do_ambiente_e_tem_ritmo_por_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QUANTILICA_SSL_VERIFY", "0")
    cliente = TransparenciaSpClient()
    assert cliente.client.verify is False
    politicas = cliente.client.host_policies
    assert politicas["www.transparencia.sp.gov.br"] is SONDAGEM_POLICY
    cliente.close()


def test_falha_da_descoberta_chega_ao_catalogo_e_nao_vira_lista_vazia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def falha(self: TransparenciaSpClient) -> list[dict]:
        raise DiscoveryError("página sem linhas")

    monkeypatch.setattr(catalog.TransparenciaSpClient, "list_historico", falha)
    with pytest.raises(DiscoveryError):
        catalog.list_datasets("historico")
    with pytest.raises(DiscoveryError):
        catalog.list_datasets()
    assert catalog._HISTORICO_CACHE is None  # a falha não fica em cache


def test_sem_o_host_instalado_usa_cliente_do_core_com_ssl_do_ambiente(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "quantilica.cli.sdk", None)
    monkeypatch.setenv("QUANTILICA_SSL_VERIFY", "0")
    cliente = TransparenciaSpClient()
    assert cliente.client.verify is False
    assert "www.transparencia.sp.gov.br" in cliente.client.host_policies
    cliente.close()


# --- link como publicado, sondagem sem baixar, 405 --------------------------


class _CorpoGrande(httpx2.SyncByteStream):
    """Corpo que acusa se alguém o lê (a sondagem nunca pode baixar)."""

    lido = 0

    def __iter__(self):
        type(self).lido += 1
        yield b"x" * 1024


def test_url_e_o_href_como_a_pagina_publica() -> None:
    """O href, resolvido contra a página, vira a URL; ``f=zip`` vem junto."""
    pagina = _pagina(_linha(2026, "Agosto", "71"), _linha(2026, "Maio", "68"))
    handler = _servidor(pagina, {"71": (200, ZIP), "68": (200, ZIP)})
    itens = _cliente(handler).list_historico()
    assert [i["url"] for i in itens] == [
        "https://www.transparencia.sp.gov.br/Remuneracao/downloadhistorico?id=68&f=zip",
        "https://www.transparencia.sp.gov.br/Remuneracao/downloadhistorico?id=71&f=zip",
    ]
    assert [i["id"] for i in itens] == ["68", "71"]


def test_href_sem_f_nao_ganha_parametro_inventado() -> None:
    pagina = (
        "<table><tr><td><strong>2026 - Agosto</strong></td><td>"
        '<a href="/Remuneracao/downloadhistorico?id=71">Baixar</a></td></tr>'
        "<tr><td><strong>2026 - Julho</strong></td><td>"
        '<a href="https://www.transparencia.sp.gov.br/Remuneracao/'
        'downloadhistorico?id=70&amp;f=zip&amp;x=1">Baixar</a></td></tr></table>'
    )
    handler = _servidor(pagina, {"70": (200, ZIP), "71": (200, ZIP)})
    itens = _cliente(handler).list_historico()
    urls = {i["id"]: i["url"] for i in itens}
    assert urls["71"].endswith("/Remuneracao/downloadhistorico?id=71")
    assert urls["70"].endswith("downloadhistorico?id=70&f=zip&x=1")
    sondados = {p[1] for p in handler.pedidos if "downloadhistorico" in p[1]}
    assert not any("f=" in u for u in sondados if u.endswith("id=71"))


def test_entidade_no_nome_do_mes_e_decodificada() -> None:
    """``Mar&ccedil;o`` é Março: o mês não pode sumir por causa da entidade."""
    pagina = _pagina(
        _linha(2024, "Mar&ccedil;o", "41"), _linha(2025, "Mar&#231;o", "53")
    )
    handler = _servidor(pagina, {"41": (200, ZIP), "53": (200, ZIP)})
    itens = _cliente(handler).list_historico()
    assert [i["label"] for i in itens] == ["2024-03", "2025-03"]


def test_sondagem_le_so_cabecalhos_com_range_e_nao_baixa_o_corpo() -> None:
    """HEAD 405 (como a fonte) cai num GET com Range, que não lê o corpo."""
    pagina = _pagina(_linha(2026, "Março", "66"))
    pedidos: list[httpx2.Request] = []
    _CorpoGrande.lido = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        pedidos.append(request)
        if request.url.path == PAGE_PATH:
            return httpx2.Response(200, text=pagina)
        if request.method == "HEAD":
            return httpx2.Response(405)
        return httpx2.Response(
            206,
            headers={"content-type": "application/octet-stream"},
            stream=_CorpoGrande(),
        )

    itens = _cliente(handler).list_historico()
    assert [i["label"] for i in itens] == ["2026-03"]
    arquivos = [r for r in pedidos if r.url.path != PAGE_PATH]
    assert [r.method for r in arquivos] == ["HEAD", "GET"]
    assert all(r.headers["range"] == SONDAGEM_HEADERS["Range"] for r in arquivos)
    assert _CorpoGrande.lido == 0


def test_405_persistente_fica_fora_sem_virar_erro_e_sem_parar_a_sondagem(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """405 no HEAD e no GET: indisponível agora, igual ao 404; só aviso."""
    pagina = _pagina(*(_linha(2026, m, str(40 + i)) for i, m in enumerate(MESES)))
    arquivos = {str(40 + i): (405, "text/plain") for i in range(8)}
    arquivos["47"] = (200, ZIP)
    handler = _servidor(pagina, arquivos)
    with caplog.at_level(logging.WARNING):
        itens = _cliente(handler).list_historico()
    assert [i["id"] for i in itens] == ["47"]  # nenhum 405 entrou como erro
    assert "não disponível agora (HTTP 405" in caplog.text
    assert "com sondagem falha" not in caplog.text
    # os 8 meses foram sondados: 405 não conta como falha seguida
    assert len({p[1] for p in handler.pedidos if "downloadhistorico" in p[1]}) == 8


def test_todos_405_e_erro_de_descoberta() -> None:
    pagina = _pagina(_linha(2026, "Agosto", "71"))
    with pytest.raises(DiscoveryError, match="404 ou 405"):
        _cliente(_servidor(pagina, {"71": (405, "text/plain")})).list_historico()


def test_cliente_padrao_tem_sondagem_barata_e_pior_caso_de_poucos_minutos() -> None:
    cliente = TransparenciaSpClient()
    assert cliente.client.timeout == SONDAGEM_TIMEOUT
    assert cliente.client.attempts == SONDAGEM_ATTEMPTS
    # 5 falhas seguidas até a parada, no pior caso de tempo esgotado em tudo.
    pior_caso = 5 * SONDAGEM_ATTEMPTS * SONDAGEM_TIMEOUT
    assert pior_caso <= 300
    cliente.close()
