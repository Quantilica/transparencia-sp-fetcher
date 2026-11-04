"""Tests for transparencia-sp-fetcher lake converter."""

from __future__ import annotations

import zipfile
from pathlib import Path

import polars as pl
from quantilica.analytics.lake import check_dataset

from transparencia_sp_fetcher.lake import converter


def test_converter_metadata() -> None:
    """Verify converter source_id and dataset list."""
    assert converter.source_id == "transparencia-sp"
    assert "remuneracao" in converter.datasets()


def test_converter_empty_dir(tmp_path: Path) -> None:
    """Test convert with empty input directory."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    lake_dir = tmp_path / "lake"
    lake_dir.mkdir()

    res = converter.convert(raw_dir, lake_dir)
    assert res.converted == 0
    assert res.skipped == 0
    assert not res.errors


def test_convert_remuneracao_csv_and_zip(tmp_path: Path) -> None:
    """Test converting raw SP payroll CSV and ZIP archives."""
    raw_dir = tmp_path / "raw" / "remuneracao"
    raw_dir.mkdir(parents=True)
    lake_dir = tmp_path / "lake"
    lake_dir.mkdir()

    # Synthetic SP Transparency Portal CSV content
    csv_content = (
        "Nome;Cargo;Orgao;Remuneracao Basica;Total Liquido;Descontos\n"
        "FULANO DE TAL;ANALISTA;SECRETARIA DA FAZENDA;1.400,50;1.200,00;200,50\n"
        "BELTRANO DA SILVA;AUDITOR;SECRETARIA DA FAZENDA;3.250,00;2.800,00;450,00\n"
    )

    # 1. Standalone CSV with YYYY-MM in filename
    csv_file = raw_dir / "remuneracao_2024-05@20261101.csv"
    csv_file.write_text(csv_content, encoding="latin-1")

    # 2. ZIP file with YYYY_MM in filename
    zip_file = raw_dir / "remuneracao_2024_06@20261101.zip"
    with zipfile.ZipFile(zip_file, "w") as zf:
        zf.writestr("Remuneracao_2024_06.csv", csv_content.encode("utf-8-sig"))

    res = converter.convert(raw_dir.parent, lake_dir)
    assert res.converted == 2
    assert not res.errors

    ds_dir = lake_dir / "transparencia-sp" / "remuneracao"
    errors = check_dataset(ds_dir)
    assert not errors, f"Lake dataset errors: {errors}"

    # Check partitions
    p_may = ds_dir / "ano=2024" / "mes=5"
    p_jun = ds_dir / "ano=2024" / "mes=6"
    assert p_may.is_dir()
    assert p_jun.is_dir()
    assert p_may.parent.name == "ano=2024"
    assert p_may.name == "mes=5"
    assert p_jun.parent.name == "ano=2024"
    assert p_jun.name == "mes=6"

    # Read parquet and verify numeric parsing and schema
    parquet_may = list(p_may.glob("*.parquet"))[0]
    df = pl.read_parquet(parquet_may)
    assert df.height == 2
    assert "remuneracao_basica" in df.columns
    assert "total_liquido" in df.columns
    assert "descontos" in df.columns
    assert df["remuneracao_basica"][0] == 1400.50
    assert df["total_liquido"][0] == 1200.00
    assert df["descontos"][0] == 200.50


def test_dicionario_nao_e_serie_mensal(tmp_path: Path) -> None:
    """dicionario_remuneracao@...xlsx e arquivo auxiliar: nao e erro nem partição."""
    raw = tmp_path / "raw" / "remuneracao"
    raw.mkdir(parents=True)
    (raw / "dicionario_remuneracao@20261030.xlsx").write_bytes(b"PK\x03\x04xlsx")
    res = converter.convert(raw.parent, tmp_path / "lake")
    assert res.errors == []
    assert res.converted == 0
    ds = tmp_path / "lake" / "transparencia-sp" / "remuneracao"
    assert not ds.is_dir() or not list(ds.glob("ano=*"))


def test_linha_com_campos_a_mais_vai_para_a_ultima_coluna(tmp_path: Path) -> None:
    """RemuneracaoAtivos.txt com `;` embutido: nenhuma linha se perde nem trunca."""
    raw = tmp_path / "raw" / "remuneracao"
    raw.mkdir(parents=True)
    txt = (
        "Nome;Cargo;Total Liquido;Observacao\n"
        "FULANO;ANALISTA;1.000,00;ok\n"
        "BELTRANO;AUDITOR;2.000,00;texto;com;separador\n"
        'CICLANO;"MEDICO; PLANTAO";3.000,00;"aspas; ok"\n'
        "DEUTRANO;FISCAL;4.000,00;ok\n"
    )
    with zipfile.ZipFile(raw / "remuneracao_2026-05@20260817.zip", "w") as zf:
        zf.writestr("RemuneracaoAtivos.txt", txt.encode("utf-8-sig"))
    res = converter.convert(raw.parent, tmp_path / "lake")
    assert res.errors == [], res.errors
    assert res.converted == 1
    ds = tmp_path / "lake" / "transparencia-sp" / "remuneracao"
    assert check_dataset(ds) == []
    df = pl.read_parquet(next((ds / "ano=2026" / "mes=5").glob("*.parquet")))
    assert df.height == 4
    assert df["nome"].to_list() == ["FULANO", "BELTRANO", "CICLANO", "DEUTRANO"]
    assert df["observacao"].to_list() == [
        "ok",
        "texto;com;separador",
        "aspas; ok",
        "ok",
    ]
    assert df["cargo"][2] == "MEDICO; PLANTAO"
    assert df["total_liquido"].to_list() == [1000.0, 2000.0, 3000.0, 4000.0]
