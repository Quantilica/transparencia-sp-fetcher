"""Descoberta dos arquivos históricos no Portal da Transparência SP."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

from quantilica.core.exceptions import FetchError
from quantilica.core.http import (
    HostPolicy,
    HttpClient,
    HttpStatusError,
    resolve_verify_from_env,
)
from quantilica.core.logging import get_logger

from .constants import (
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

# Rótulo da linha da tabela: ``<strong>2026 - Agosto</strong>``.
_LABEL_RE = re.compile(r"^\s*(\d{4})\s*-\s*(.+?)\s*$")
# Link de download da mesma linha: ``.../downloadhistorico?id=71&f=zip``.
_LINK_RE = re.compile(r"downloadhistorico\?(?:[^#]*&)?id=(\d+)", re.IGNORECASE)

# Sondagem dos meses listados: um HEAD (ou GET só de cabeçalhos) por mês, com ritmo
# próprio para não parecer varredura ao firewall da fonte.
SONDAGEM_POLICY = HostPolicy(
    min_interval=0.5,
    max_concurrency=1,
    backoff_base=15.0,
    backoff_max=120.0,
)
# Falhas seguidas (que não sejam 404) a partir das quais a sondagem para: a fonte
# está bloqueando ou fora do ar, e esperar o retry de dezenas de meses não ajuda.
_MAX_FALHAS_SEGUIDAS = 5


class DiscoveryError(FetchError):
    """A página de remuneração não pôde ser lida ou não tem mais a forma esperada."""


@dataclass(frozen=True)
class LinhaHistorico:
    """Uma linha da tabela da página: o mês e, se houver, o id do arquivo."""

    ano: int
    mes_nome: str
    file_id: str | None


class _TabelaHistorico(HTMLParser):
    """Lê a página linha a linha: cada ``<tr>`` tem seu rótulo e seu link.

    Um mês sem link fica com ``file_id=None``; nunca herda o id da linha vizinha.
    Quando a marcação não usa ``<tr>``, um novo rótulo também abre uma nova linha.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.linhas: list[LinhaHistorico] = []
        self.links_sem_rotulo = 0
        self._rotulo: tuple[int, str] | None = None
        self._file_id: str | None = None
        self._em_strong = False
        self._texto: list[str] = []

    def _fecha_linha(self) -> None:
        if self._rotulo is not None:
            ano, mes_nome = self._rotulo
            self.linhas.append(LinhaHistorico(ano, mes_nome, self._file_id))
        elif self._file_id is not None:
            self.links_sem_rotulo += 1
        self._rotulo = None
        self._file_id = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._fecha_linha()
        elif tag == "strong":
            self._em_strong = True
            self._texto = []
        elif tag == "a":
            href = dict(attrs).get("href") or ""
            achado = _LINK_RE.search(href)
            if achado and self._file_id is None:
                self._file_id = achado.group(1)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr":
            self._fecha_linha()
        elif tag == "strong" and self._em_strong:
            self._em_strong = False
            achado = _LABEL_RE.match("".join(self._texto))
            if achado:
                if self._rotulo is not None:
                    self._fecha_linha()
                self._rotulo = (int(achado.group(1)), achado.group(2))

    def handle_data(self, data: str) -> None:
        if self._em_strong:
            self._texto.append(data)

    def termina(self) -> None:
        """Fecha o documento e a última linha, se ficou aberta."""
        self.close()
        self._fecha_linha()


def parse_historico_page(html: str) -> tuple[list[LinhaHistorico], int]:
    """Extrai da página as linhas ``AAAA - Mês`` com o id do arquivo de cada uma.

    Args:
        html: HTML da página de remuneração.

    Returns:
        As linhas reconhecidas (com ``file_id`` ``None`` quando a linha não tem
        link) e quantos links de download apareceram em linhas sem rótulo de mês.
    """
    parser = _TabelaHistorico()
    parser.feed(html)
    parser.termina()
    return parser.linhas, parser.links_sem_rotulo


def _default_http_client() -> HttpClient:
    """Cliente padrão do host (``QUANTILICA_HTTP_*``, SSL, CA), com plano B do core."""
    try:
        from quantilica.cli.sdk import default_client
    except ImportError:  # CLI autônoma, sem o host instalado
        return HttpClient(verify=resolve_verify_from_env(), emulate_browser=True)
    return default_client()


class TransparenciaSpClient:
    """Descobre os arquivos mensais publicados na página de remuneração."""

    def __init__(
        self,
        *,
        base_url: str = TRANSPARENCIA_SP_BASE_URL,
        client: HttpClient | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        if client is None:
            client = _default_http_client()
            host = self.base_url.split("//", 1)[-1].split("/", 1)[0].lower()
            client.host_policies.setdefault(host, SONDAGEM_POLICY)
        self.client = client
        self.logger = logger or get_logger(__name__)

    def close(self) -> None:
        """Fecha o cliente HTTP."""
        self.client.close()

    def _ler_pagina(self) -> str:
        try:
            return self.client.get(REMUNERACAO_PAGE_URL).text
        except Exception as exc:
            raise DiscoveryError(
                f"Página de remuneração ilegível ({REMUNERACAO_PAGE_URL}): {exc}"
            ) from exc

    def _sondar(self, item: dict[str, Any]) -> str:
        """Sonda o arquivo do mês: ``ok``, ``nao_publicado`` ou ``falhou``.

        404 é a resposta esperada da fonte para um mês listado e ainda não
        publicado. Qualquer outra coisa (exceção, 403, 429, 5xx, HTML no lugar do
        arquivo) não prova que o arquivo não existe: é ``falhou``.
        """
        try:
            probe = self.client.head_or_get(item["url"])
        except Exception as exc:  # noqa: BLE001 - qualquer falha de rede ou de status
            if isinstance(exc, HttpStatusError) and exc.status_code == 404:
                self.logger.warning(
                    "Histórico %s listado na página, mas ainda não publicado "
                    "(HTTP 404): fora do catálogo",
                    item["label"],
                )
                return "nao_publicado"
            self.logger.warning(
                "Histórico %s: sondagem falhou (%s): %s",
                item["label"],
                item["url"],
                exc,
            )
            return "falhou"
        tipo = (probe.headers.get("content-type") or "").lower()
        if probe.status_code not in (200, 206) or tipo.startswith("text/html"):
            self.logger.warning(
                "Histórico %s: sondagem inesperada (HTTP %s, %s): %s",
                item["label"],
                probe.status_code,
                tipo or "sem content-type",
                item["url"],
            )
            return "falhou"
        return "ok"

    def list_historico(self) -> list[dict[str, Any]]:
        """Descobre os arquivos históricos reais na página de remuneração.

        O endpoint ``downloadhistorico`` não aceita ``ano``/``mes``: cada mês
        tem um ``id`` numérico publicado na tabela da página. A descoberta lê
        essa tabela, linha a linha, para não depender de ids fixos.

        Cada mês com link é sondado. 404 é "ainda não publicado" e o mês fica de
        fora (registrado em ``warning``). Falha de qualquer outro tipo na sondagem
        (exceção, 403, 429, 5xx, HTML no lugar do arquivo) não prova ausência: o
        mês entra no catálogo assim mesmo e o download decide, contando o erro (o
        ``sync`` sai 3 ou 1). Assim um bloqueio da fonte nunca esvazia a série
        em silêncio.

        Returns:
            Lista de dicts com ``id``, ``ano``, ``mes``, ``label`` e ``url``.

        Raises:
            DiscoveryError: A página não pôde ser lida, não tem nenhuma linha
                ``AAAA - Mês`` reconhecível ou nenhuma linha com link utilizável
                (a marcação mudou), ou todos os meses listados deram 404.
        """
        linhas, links_sem_rotulo = parse_historico_page(self._ler_pagina())
        if links_sem_rotulo:
            self.logger.warning(
                "%d link(s) downloadhistorico em linha sem rótulo 'AAAA - Mês': "
                "ignorados",
                links_sem_rotulo,
            )
        if not linhas:
            raise DiscoveryError(
                "Nenhuma linha 'AAAA - Mês' reconhecida na página de remuneração "
                f"({REMUNERACAO_PAGE_URL}): a marcação mudou?"
            )

        itens: list[dict[str, Any]] = []
        for linha in linhas:
            mes = _MESES.get(linha.mes_nome.strip().lower())
            if mes is None:
                self.logger.warning(
                    "Histórico %s - %s: mês desconhecido, ignorado",
                    linha.ano,
                    linha.mes_nome,
                )
                continue
            label = f"{linha.ano}-{mes:02d}"
            if linha.file_id is None:
                self.logger.warning(
                    "Histórico %s listado na página sem link de download: "
                    "fora do catálogo",
                    label,
                )
                continue
            itens.append(
                {
                    "id": linha.file_id,
                    "ano": linha.ano,
                    "mes": mes,
                    "label": label,
                    "url": f"{DOWNLOAD_HISTORICO_URL}?id={linha.file_id}&f=zip",
                }
            )
        if not itens:
            raise DiscoveryError(
                f"{len(linhas)} linha(s) reconhecida(s) na página de remuneração, "
                "nenhuma com mês conhecido e link de download: a marcação mudou?"
            )

        arquivos: list[dict[str, Any]] = []
        falhas: list[str] = []
        nao_publicados = 0
        seguidas = 0
        for posicao, item in enumerate(itens):
            if seguidas >= _MAX_FALHAS_SEGUIDAS:
                restantes = itens[posicao:]
                self.logger.warning(
                    "Sondagem interrompida após %d falhas seguidas: %d mês(es) "
                    "entram no catálogo sem sondagem (o download decide)",
                    seguidas,
                    len(restantes),
                )
                arquivos.extend(restantes)
                break
            resultado = self._sondar(item)
            if resultado == "falhou":
                seguidas += 1
                falhas.append(item["label"])
                arquivos.append(item)
                continue
            seguidas = 0
            if resultado == "ok":
                arquivos.append(item)
            else:
                nao_publicados += 1
        if falhas:
            self.logger.warning(
                "%d mês(es) com sondagem falha entram no catálogo (o download "
                "decide e conta o erro): %s",
                len(falhas),
                ", ".join(falhas),
            )
        if not arquivos:
            raise DiscoveryError(
                f"Todos os {nao_publicados} mês(es) listados na página de remuneração "
                "deram 404: nenhum arquivo histórico publicado?"
            )
        return sorted(arquivos, key=lambda a: (a["ano"], a["mes"]))
