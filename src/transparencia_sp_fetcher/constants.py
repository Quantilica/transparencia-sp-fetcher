"""Constants and endpoint definitions for transparencia-sp-fetcher."""

from __future__ import annotations

TRANSPARENCIA_SP_BASE_URL = "https://www.transparencia.sp.gov.br"
DOWNLOAD_CORRENTE_URL = (
    f"{TRANSPARENCIA_SP_BASE_URL}/Remuneracao/Download?arquivo=Remuneracao.csv"
)
DOWNLOAD_HISTORICO_URL = f"{TRANSPARENCIA_SP_BASE_URL}/Remuneracao/downloadhistorico"
DOWNLOAD_RAR_URL = f"{TRANSPARENCIA_SP_BASE_URL}/PortalTransparencia-Report/historico"
DICIONARIO_URL = (
    f"{TRANSPARENCIA_SP_BASE_URL}/Dicionarios/"
    "Dicionario%20de%20dados%20-%20Remuneracao.xlsx"
)

START_YEAR = 2012
