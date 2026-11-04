"""Série antiga (RAR) e períodos do lake de transparencia-sp."""

from __future__ import annotations

import zipfile
from pathlib import Path

import polars as pl
import pytest
from quantilica.analytics.lake import check_dataset

from transparencia_sp_fetcher import lake
from transparencia_sp_fetcher.lake import (
    RarUnavailableError,
    _extract_year_month,
    converter,
)

from .rar_fixture import make_rar4

# Cabeçalho da era 2013-2016 (TOT*_FINAL) em latin-1, com acento e CRLF.
CSV_2013 = (
    "NOME;CARGO;TOTMES_FINAL;TOTBRU_FINAL;TOTLIQ_FINAL\r\n"
    "JOÃO DA SILVA;ANALISTA;1.400,50;1.600,00;1.200,25\r\n"
    "MARIA SOUZA;AUDITORA;3.250,00;3.500,00;2.800,00\r\n"
).encode("latin-1")


def _libarchive_ok() -> bool:
    try:
        lake._libarchive()
    except RarUnavailableError:
        return False
    return True


needs_rar = pytest.mark.skipif(not _libarchive_ok(), reason="libarchive indisponível")


def _lake(tmp_path: Path) -> tuple[Path, Path, Path]:
    raw = tmp_path / "raw" / "rar"
    raw.mkdir(parents=True)
    lk = tmp_path / "lake"
    lk.mkdir()
    return raw, lk, lk / "transparencia-sp" / "remuneracao"


@needs_rar
def test_rar_multimembro_streaming_chave_composta(tmp_path: Path) -> None:
    raw, lk, ds = _lake(tmp_path)
    (raw / "remuneracao_rar_2013-02@20261101.rar").write_bytes(
        make_rar4(
            [
                ("remuneracao_Fevereiro_2013.txt", CSV_2013),
                ("outra_parte.txt", CSV_2013.replace(b"JO\xc3O", b"JOSE")),
                ("LEIAME.pdf", b"%PDF"),  # não é dado: ignorado
            ]
        )
    )
    res = converter.convert(raw.parent, lk)
    assert not res.errors, res.errors
    assert res.converted == 2  # os dois membros, não só o primeiro
    assert not check_dataset(ds)
    df = pl.read_parquet(list((ds / "ano=2013" / "mes=2").glob("*.parquet")))
    assert df.height == 4
    assert "JOÃO DA SILVA" in df["nome"].to_list()  # latin-1 estrito, sem U+FFFD
    assert df["totmes_final"][0] == 1400.50
    assert df["totliq_final"][1] == 2800.00
    # reconversão: nada novo, os dois membros contam como já convertidos
    res2 = converter.convert(raw.parent, lk)
    assert (res2.converted, res2.skipped, res2.errors) == (0, 2, [])


@needs_rar
def test_rar_truncado_vira_erro_contado(tmp_path: Path) -> None:
    raw, lk, _ = _lake(tmp_path)
    data = make_rar4([("a.txt", CSV_2013)])
    # download truncado no meio dos dados do membro
    (raw / "remuneracao_rar_2013-03@20261101.rar").write_bytes(data[: len(data) - 40])
    res = converter.convert(raw.parent, lk)
    assert res.converted == 0
    assert res.errors


def test_rar_sem_libarchive_erro_claro(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw, lk, _ = _lake(tmp_path)
    (raw / "remuneracao_rar_2013-02@20261101.rar").write_bytes(
        b"Rar!\x1a\x07\x00" + b"\x00" * 16
    )

    def boom():
        raise RarUnavailableError("libarchive ausente; instale transparencia-sp[rar]")

    monkeypatch.setattr(lake, "_libarchive", boom)
    res = converter.convert(raw.parent, lk)
    assert res.converted == 0
    assert len(res.errors) == 1 and "libarchive" in res.errors[0]


def test_zip_multimembro_nao_perde_linhas(tmp_path: Path) -> None:
    raw, lk, ds = _lake(tmp_path)
    csv = "Nome;Total Liquido\nA;1.000,00\nB;2.000,00\n"
    with zipfile.ZipFile(raw / "remuneracao_2024-06@20261101.zip", "w") as zf:
        zf.writestr("parte1.txt", csv.encode("utf-8-sig"))
        zf.writestr("parte2.txt", csv.replace("A;", "C;").encode("utf-8-sig"))
    res = converter.convert(raw.parent, lk)
    assert res.converted == 2 and not res.errors
    df = pl.read_parquet(list((ds / "ano=2024" / "mes=6").glob("*.parquet")))
    assert sorted(df["nome"].to_list()) == ["A", "B", "B", "C"]


def test_byte_invalido_vira_erro_sem_replace(tmp_path: Path) -> None:
    raw, lk, _ = _lake(tmp_path)
    bad = "Nome;Total Liquido\nJÃO;1,00\n".encode() + b"\x81\x8d\n"
    (raw / "remuneracao_2024-07@20261101.csv").write_bytes(bad)
    res = converter.convert(raw.parent, lk)
    assert res.converted == 0 and res.errors


def test_corrente_particiona_pelo_mes_do_carimbo(tmp_path: Path) -> None:
    raw, lk, ds = _lake(tmp_path)
    (raw / "remuneracao_corrente@20261024.csv").write_bytes(
        "Nome;Total Liquido (R$)\nA;1.400,00\n".encode("utf-8-sig")
    )
    res = converter.convert(raw.parent, lk)
    assert res.converted == 1 and not res.errors
    assert (ds / "ano=2026" / "mes=10").is_dir()
    assert not (ds / "ano=2024").exists()


def test_sem_periodo_nao_assume_2024_01(tmp_path: Path) -> None:
    raw, lk, ds = _lake(tmp_path)
    (raw / "dados_sem_periodo.csv").write_text("Nome;Total\nA;1,00\n")
    (raw / "remuneracao_corrente.csv").write_text("Nome;Total\nA;1,00\n")  # sem carimbo
    res = converter.convert(raw.parent, lk)
    assert res.converted == 0
    assert len(res.errors) == 2
    assert not ds.exists() or not list(ds.rglob("*.parquet"))


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("remuneracao_2024-05@20261101.csv", (2024, 5)),
        ("remuneracao_rar_2012-06@20261101.rar", (2012, 6)),
        ("remuneracao_corrente@20261024.csv", (2026, 10)),
        ("remuneracao_corrente@20261301.csv", None),  # mês 13 inválido
        ("remuneracao_2024-13@20261101.csv", None),
        ("qualquer@20261101.csv", None),  # carimbo só vale para o corrente
    ],
)
def test_extract_year_month(nome: str, esperado: tuple[int, int] | None) -> None:
    assert _extract_year_month(nome) == esperado
