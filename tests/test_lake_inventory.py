"""O inventário do conversor diz à auditoria do lake o que não vira Parquet."""

from __future__ import annotations

import zipfile
from pathlib import Path

from transparencia_sp_fetcher.lake import converter

CSV = "Nome;Cargo\nFULANO;ANALISTA\n"


def _zip(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("remuneracao.csv", CSV.encode("utf-8-sig"))


def _toque(path: Path, conteudo: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(conteudo)


def _plano(raw: Path) -> dict[str, tuple[str | None, str | None]]:
    return {
        p.path.relative_to(raw).as_posix(): (p.dataset, p.skip_reason)
        for p in converter.inventory(raw)
    }


def test_inventory_derivados_de_mes_com_conteiner_sao_gemeos(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _toque(raw / "rar" / "remuneracao_rar_2012-06@20130805.rar")
    _zip(raw / "historico" / "remuneracao_2023-04@20260521.zip")
    # Parquets do acervo: o mesmo mês já existe como contêiner que o conversor lê.
    _toque(raw / "derivados" / "remuneracao_2012-06@20240903.parquet")
    _toque(raw / "derivados" / "remuneracao_2023-04@20240903.parquet")

    plano = _plano(raw)

    assert plano["derivados/remuneracao_2012-06@20240903.parquet"] == (None, "gemeo")
    assert plano["derivados/remuneracao_2023-04@20240903.parquet"] == (None, "gemeo")
    # Os contêineres continuam esperando Parquet.
    assert plano["rar/remuneracao_rar_2012-06@20130805.rar"] == ("remuneracao", None)
    assert plano["historico/remuneracao_2023-04@20260521.zip"] == ("remuneracao", None)


def test_inventory_derivado_sem_conteiner_do_mes_continua_esperando_parquet(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw"
    _toque(raw / "rar" / "remuneracao_rar_2012-06@20130805.rar")
    # 2012-07 só existe como derivado: o conversor não o lê, a auditoria deve acusar.
    _toque(raw / "derivados" / "remuneracao_2012-07@20240903.parquet")
    # Contêiner de outro mês não cobre o derivado.
    _toque(raw / "derivados" / "remuneracao_2013-01@20240903.parquet")

    plano = _plano(raw)

    assert plano["derivados/remuneracao_2012-07@20240903.parquet"] == (
        "remuneracao",
        None,
    )
    assert plano["derivados/remuneracao_2013-01@20240903.parquet"] == (
        "remuneracao",
        None,
    )


def test_inventory_conteiner_antigo_nao_cobre_o_derivado(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    # Só a versão vigente do contêiner conta: a antiga é superada.
    _toque(raw / "rar" / "remuneracao_rar_2012-06@20120801.rar")
    _toque(raw / "rar" / "remuneracao_rar_2012-06@20130805.rar")
    _toque(raw / "derivados" / "remuneracao_2012-06@20240903.parquet")

    plano = _plano(raw)

    assert plano["rar/remuneracao_rar_2012-06@20120801.rar"] == (None, "superado")
    assert plano["rar/remuneracao_rar_2012-06@20130805.rar"] == ("remuneracao", None)
    assert plano["derivados/remuneracao_2012-06@20240903.parquet"] == (None, "gemeo")


def test_inventory_dicionario_e_nao_tabular(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    # XLSX é um ZIP: nem pela assinatura o conversor o toma por dado.
    _zip(raw / "dicionario" / "dicionario_remuneracao@20261123.xlsx")
    _toque(raw / "dicionario" / "dicionario_remuneracao@20261030.xlsx")
    _toque(raw / "corrente" / "remuneracao_corrente@20261024.csv", CSV.encode())
    _toque(raw / "corrente" / "leiame.txt")
    _toque(raw / "corrente" / "remuneracao_2026-10@20261024.csv.tmp")
    _toque(raw / "corrente" / "remuneracao_corrente@20261024.csv.manifest.json")

    plano = _plano(raw)

    assert plano["dicionario/dicionario_remuneracao@20261123.xlsx"] == (
        None,
        "nao_tabular",
    )
    # A versão antiga do dicionário também não é dado (auxiliar vem antes de superado).
    assert plano["dicionario/dicionario_remuneracao@20261030.xlsx"] == (
        None,
        "nao_tabular",
    )
    assert plano["corrente/remuneracao_corrente@20261024.csv"] == ("remuneracao", None)
    assert plano["corrente/leiame.txt"] == (None, "nao_tabular")
    # Sidecars e temporários não são brutos.
    assert len(plano) == 4


def test_inventory_arquivo_de_outro_formato_e_nao_tabular(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _toque(raw / "rar" / "remuneracao_rar_2012-06@20130805.rar")
    _toque(raw / "rar" / "notas_2012.pdf")

    assert _plano(raw)["rar/notas_2012.pdf"] == (None, "nao_tabular")


def test_inventory_sem_pasta(tmp_path: Path) -> None:
    assert converter.inventory(tmp_path / "nao-existe") == []
