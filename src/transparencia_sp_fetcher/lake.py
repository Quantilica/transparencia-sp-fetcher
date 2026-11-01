"""Universal Hive Parquet Lake converter for transparencia-sp-fetcher."""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from collections.abc import Sequence
from pathlib import Path

try:
    import polars as pl
    from quantilica.analytics.lake import ConvertResult, LakeWriter
    from quantilica.core.lake import (
        DatasetDescriptor,
        partition_types_for,
        select_current,
    )
except ImportError as exc:
    raise ImportError(
        "transparencia_sp_fetcher.lake requer o extra 'analysis': "
        "uv add 'transparencia-sp-fetcher[analysis]' "
        "--index https://index.quantilica.com/simple/"
    ) from exc

SOURCE_ID = "transparencia-sp"
DATASETS = ["remuneracao"]


def _norm_col(col_name: str) -> str:
    s = unicodedata.normalize("NFKD", col_name)
    s = s.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _read_csv_members(path: Path) -> list[tuple[str, bytes]]:
    """Return list of (member_name, bytes) for CSV/TXT in file (or ZIP archive)."""
    try:
        with open(path, "rb") as f:
            header = f.read(4)
        if header.startswith(b"PK"):
            results = []
            with zipfile.ZipFile(path) as zf:
                for name in zf.namelist():
                    if name.lower().endswith((".csv", ".txt")):
                        results.append((name, zf.read(name)))
            return results
    except Exception:
        pass

    if path.suffix.lower() in (".csv", ".txt"):
        return [(path.name, path.read_bytes())]
    return []


def _extract_year_month(filename: str) -> tuple[int, int]:
    """Extract (year, month) from filename or stamp."""
    s = filename.lower()
    m = re.search(r"(\d{4})[-_](\d{1,2})", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    # Check YYYYMM format
    m2 = re.search(r"(\d{4})(\d{2})", s)
    if m2:
        return int(m2.group(1)), int(m2.group(2))
    return 2024, 1


class TransparenciaSpLakeConverter:
    """Converts SP public servant payroll data into Universal Hive Parquet Lake."""

    def __init__(self, source_id: str = SOURCE_ID) -> None:
        self.source_id = source_id

    def datasets(self) -> list[str]:
        """Return available dataset identifiers."""
        return list(DATASETS)

    def convert(
        self,
        input_dir: Path,
        lake_dir: Path,
        *,
        datasets: Sequence[str] | None = None,
        force: bool = False,
    ) -> ConvertResult:
        res = ConvertResult()
        input_path = Path(input_dir)
        lake_path = Path(lake_dir)

        if not input_path.exists():
            return res

        target_datasets = set(datasets or DATASETS)
        if "remuneracao" not in target_datasets:
            return res

        # Initialize LakeWriter for remuneracao
        descriptor = DatasetDescriptor(
            source_id=self.source_id,
            dataset_id="remuneracao",
            alias="remuneracao",
            partition_keys=["ano", "mes"],
            partition_types=partition_types_for(["ano", "mes"]),
        )
        writer = LakeWriter(
            lake_path / self.source_id / "remuneracao", descriptor, force=force
        )

        # Gather active raw files
        all_raw_files = [f for f in input_path.rglob("*") if f.is_file()]
        active_files = select_current(all_raw_files)

        for raw_file in active_files:
            members = _read_csv_members(raw_file)
            if not members:
                continue

            ano, mes = _extract_year_month(raw_file.name)

            for name, data_bytes in members:
                try:
                    # Try UTF-8 with BOM first, fallback to latin-1
                    try:
                        text = data_bytes.decode("utf-8-sig")
                    except UnicodeDecodeError:
                        text = data_bytes.decode("latin-1", errors="replace")

                    df = pl.read_csv(
                        io.StringIO(text),
                        separator=";",
                        infer_schema_length=5000,
                    )
                    if df.height == 0:
                        continue

                    # Normalize column names
                    df = df.rename({c: _norm_col(c) for c in df.columns})

                    # Numeric cleaning for monetary columns (e.g. 1.400,00 -> 1400.00)
                    monetary_cols = [
                        c
                        for c in df.columns
                        if any(
                            term in c
                            for term in (
                                "remuneracao",
                                "salario",
                                "ferias",
                                "pagamentos",
                                "licenca",
                                "abono",
                                "redutor",
                                "total_liquido",
                                "liquido",
                                "bruto",
                                "descontos",
                            )
                        )
                    ]
                    for col in monetary_cols:
                        df = df.with_columns(
                            pl.col(col)
                            .cast(pl.Utf8)
                            .str.replace_all(r"\.", "")
                            .str.replace(",", ".")
                            .cast(pl.Float64, strict=False)
                            .alias(col)
                        )

                    # Add partition columns
                    df = df.with_columns(
                        pl.lit(ano).cast(pl.Int32).alias("ano"),
                        pl.lit(mes).cast(pl.Int32).alias("mes"),
                    )

                    writer.write_polars(
                        df,
                        src=raw_file,
                        partitions={"ano": ano, "mes": mes},
                    )
                    res.converted += 1
                except Exception as exc:
                    res.errors.append(
                        f"Erro ao converter {name} em {raw_file.name}: {exc}"
                    )

        return res


converter = TransparenciaSpLakeConverter()
