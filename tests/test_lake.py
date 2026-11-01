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
