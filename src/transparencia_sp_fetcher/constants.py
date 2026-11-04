"""Constants and endpoint definitions for transparencia-sp-fetcher."""

from __future__ import annotations

TRANSPARENCIA_SP_BASE_URL = "https://www.transparencia.sp.gov.br"
DOWNLOAD_CORRENTE_URL = (
    f"{TRANSPARENCIA_SP_BASE_URL}/Remuneracao/Download?arquivo=Remuneracao.csv"
)
DOWNLOAD_HISTORICO_URL = f"{TRANSPARENCIA_SP_BASE_URL}/Remuneracao/downloadhistorico"
REMUNERACAO_PAGE_URL = f"{TRANSPARENCIA_SP_BASE_URL}/Remuneracao"
# Série histórica antiga (jun/2012 a mar/2023 no lake): um RAR v4 por mês, fora da
# página atual. O nome leva o mês por extenso; março é ``Março`` até 2016 e ``Marco``
# de 2017 em diante (varredura de 27/10/2026).
RAR_BASE_URL = f"{TRANSPARENCIA_SP_BASE_URL}/PortalTransparencia-Report/historico"
RAR_START = (2012, 6)
RAR_END = (2023, 3)
RAR_MESES = (
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)
DICIONARIO_URL = (
    f"{TRANSPARENCIA_SP_BASE_URL}/Dicionarios/"
    "Dicionario%20de%20dados%20-%20Remuneracao.xlsx"
)

START_YEAR = 2012


def rar_url(ano: int, mes: int) -> str:
    """URL do RAR mensal da série antiga (``Março`` até 2016, ``Marco`` depois)."""
    from urllib.parse import quote

    nome = RAR_MESES[mes - 1]
    if mes == 3 and ano >= 2017:
        nome = "Marco"
    return f"{RAR_BASE_URL}/remuneracao_{quote(nome)}_{ano}.rar"
