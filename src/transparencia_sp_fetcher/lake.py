"""Universal Hive Parquet Lake converter for transparencia-sp-fetcher."""

from __future__ import annotations

import codecs
import csv
import logging
import os
import re
import tempfile
import unicodedata
import zipfile
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

try:
    import polars as pl
    from quantilica.analytics.lake import ConvertResult, LakeWriter
    from quantilica.core.lake import (
        DatasetDescriptor,
        composite_file_key,
        partition_types_for,
        select_current,
    )
except ImportError as exc:
    raise ImportError(
        "transparencia_sp_fetcher.lake requer o extra 'analysis': "
        "uv add 'transparencia-sp-fetcher[analysis]' "
        "--index https://index.quantilica.com/simple/"
    ) from exc

logger = logging.getLogger(__name__)

SOURCE_ID = "transparencia-sp"
DATASETS = ["remuneracao"]


def _norm_col(col_name: str) -> str:
    s = unicodedata.normalize("NFKD", col_name)
    s = s.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


class RarUnavailableError(RuntimeError):
    """Leitura de RAR indisponível neste ambiente (falta libarchive)."""


_RAR_SIGNATURE = b"Rar!\x1a\x07"
_CHUNK = 1 << 20
_MEMBER_SUFFIXES = (".csv", ".txt")
#: Codificação por contêiner, em ordem de tentativa (decodificação estrita).
#: RAR antigo: latin-1 (CRLF, sem BOM); ZIP/CSV atuais: UTF-8 com BOM.
_ENCODINGS = {
    "rar": ("latin-1",),
    "zip": ("utf-8-sig", "cp1252"),
    "plain": ("utf-8-sig", "cp1252"),
}


def _libarchive():
    """Importa ``libarchive-c`` com erro claro quando ele ou a lib do sistema faltam."""
    try:
        import libarchive
    except (ImportError, OSError) as exc:
        raise RarUnavailableError(
            "Ler a série antiga (RAR) requer o pacote 'libarchive-c' e a biblioteca "
            "libarchive do sistema (Fedora: libarchive; Debian/Ubuntu: libarchive13). "
            "O 7zip do Fedora não tem codec RAR. Instale com: "
            "uv add 'transparencia-sp-fetcher[rar]' "
            f"({exc})"
        ) from exc
    return libarchive


def _container_kind(path: Path) -> str:
    """Tipo do arquivo pela assinatura (nunca pela extensão)."""
    with open(path, "rb") as fh:
        head = fh.read(8)
    if head.startswith(b"PK"):
        return "zip"
    if head.startswith(_RAR_SIGNATURE):
        return "rar"
    return "plain"


def _is_data_member(name: str) -> bool:
    return name.lower().endswith(_MEMBER_SUFFIXES)


def _member_names(path: Path, kind: str) -> list[str | None]:
    """Nomes dos membros de dados; ``[None]`` para CSV/TXT solto."""
    if kind == "zip":
        with zipfile.ZipFile(path) as zf:
            return [
                i.filename
                for i in zf.infolist()
                if not i.is_dir() and _is_data_member(i.filename)
            ]
    if kind == "rar":
        la = _libarchive()
        with la.file_reader(str(path)) as archive:
            return [
                e.pathname
                for e in archive
                if not e.isdir and _is_data_member(e.pathname)
            ]
    return [None] if path.suffix.lower() in _MEMBER_SUFFIXES else []


def _member_chunks(path: Path, kind: str, name: str | None) -> Iterator[bytes]:
    """Bytes do membro em blocos (streaming: nunca o membro inteiro em memória)."""
    if kind == "zip":
        with zipfile.ZipFile(path) as zf, zf.open(name or "") as fh:
            while chunk := fh.read(_CHUNK):
                yield chunk
    elif kind == "rar":
        la = _libarchive()
        with la.file_reader(str(path)) as archive:
            for entry in archive:
                if entry.pathname == name:
                    yield from entry.get_blocks(_CHUNK)
                    return
        raise FileNotFoundError(f"membro {name!r} ausente em {path.name}")
    else:
        with open(path, "rb") as fh:
            while chunk := fh.read(_CHUNK):
                yield chunk


def _transcode_to_utf8(chunks: Iterable[bytes], dest: Path, encoding: str) -> None:
    """Decodifica em streaming (estrito) e grava UTF-8 sem BOM."""
    decoder = codecs.getincrementaldecoder(encoding)(errors="strict")
    with open(dest, "w", encoding="utf-8", newline="") as out:
        for chunk in chunks:
            out.write(decoder.decode(chunk))
        out.write(decoder.decode(b"", final=True))


@contextmanager
def _member_as_utf8(path: Path, kind: str, name: str | None) -> Iterator[Path]:
    """CSV do membro em UTF-8 num diretório temporário.

    ``QUANTILICA_LAKE_SCRATCH`` move o temporário para outro disco. Byte inválido na
    última codificação da lista vira erro (sem ``errors="replace"``).
    """
    attempts = _ENCODINGS[kind]
    with tempfile.TemporaryDirectory(
        dir=os.environ.get("QUANTILICA_LAKE_SCRATCH") or None
    ) as tmp:
        dest = Path(tmp) / "membro.csv"
        for idx, enc in enumerate(attempts):
            try:
                _transcode_to_utf8(_member_chunks(path, kind, name), dest, enc)
                break
            except UnicodeDecodeError:
                if idx == len(attempts) - 1:
                    raise
        yield dest


_PERIODO_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})[-_](0[1-9]|1[0-2])(?!\d)")
_CARIMBO_RE = re.compile(r"@((?:19|20)\d{2})(0[1-9]|1[0-2])[0-3]\d")


def _extract_year_month(filename: str) -> tuple[int, int] | None:
    """Período (ano, mês) de um arquivo bruto, ou ``None`` se não for inferível.

    O período vem do nome (``..._2024-05@...``). Só o arquivo **corrente**, que não
    tem mês de referência no conteúdo, usa o mês do carimbo ``@AAAAMMDD`` (data de
    ``Last-Modified``). Sem nenhum dos dois não há padrão: o chamador conta erro.
    """
    base, _, stamp = filename.partition("@")
    m = _PERIODO_RE.search(base)
    if m:
        return int(m.group(1)), int(m.group(2))
    if "corrente" in base.lower():
        c = _CARIMBO_RE.search("@" + stamp)
        if c:
            return int(c.group(1)), int(c.group(2))
    return None


_AUXILIARY_RE = re.compile(r"^(dicionario|leiame|leia_me|readme)", re.IGNORECASE)


def _is_auxiliary(filename: str) -> bool:
    """Arquivo que acompanha a série mas não é dado mensal (dicionário, leia-me).

    Não tem período, não vira partição ``ano/mes`` e não é erro.
    """
    base = unicodedata.normalize("NFKD", filename.partition("@")[0])
    base = base.encode("ascii", "ignore").decode("ascii")
    return bool(_AUXILIARY_RE.match(base))


def _is_ragged_error(exc: BaseException) -> bool:
    return "more fields than defined" in str(exc)


def repair_ragged_csv(src: Path, dst: Path) -> int:
    """Reescreve ``src`` juntando os campos excedentes na última coluna.

    Critério: o número de colunas é o do cabeçalho; numa linha com mais campos, os
    excedentes são unidos, com ``;``, ao último campo (texto com separador
    embutido). A leitura respeita aspas e uma linha continua sendo um registro:
    nenhuma é descartada nem truncada. Devolve quantas linhas foram alteradas.
    """
    changed = 0
    with (
        open(src, encoding="utf-8", newline="") as fin,
        open(dst, "w", encoding="utf-8", newline="") as fout,
    ):
        reader = csv.reader(fin, delimiter=";")
        writer = csv.writer(fout, delimiter=";", lineterminator="\n")
        header = next(reader, None)
        if header is None:
            return 0
        width = len(header)
        writer.writerow(header)
        for row in reader:
            if len(row) > width:
                row = [*row[: width - 1], ";".join(row[width - 1 :])]
                changed += 1
            writer.writerow(row)
    return changed


_MONETARY_TERMS = (
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


def _is_monetary(col: str) -> bool:
    # eras antigas: TOTDOMES/TOTBRUTO/TOTLIQ (2012) e TOT*_FINAL (2013-2016)
    return col.startswith("tot") or any(t in col for t in _MONETARY_TERMS)


def _member_frame(csv_path: Path, partitions: dict[str, int]) -> pl.LazyFrame | None:
    """Plano lazy (streaming) de um membro, ou ``None`` se só tiver cabeçalho.

    Tudo é lido como texto; só as colunas monetárias viram ``Float64`` (``1.400,50``).
    """
    lf = pl.scan_csv(csv_path, separator=";", infer_schema=False, encoding="utf8")
    if lf.head(1).collect().height == 0:
        return None
    names = {c: _norm_col(c) for c in lf.collect_schema().names()}
    lf = lf.rename(names)
    for col in (n for n in names.values() if _is_monetary(n)):
        lf = lf.with_columns(
            pl.col(col)
            .str.replace_all(r"\.", "")
            .str.replace(",", ".", literal=True)
            .cast(pl.Float64, strict=False)
            .alias(col)
        )
    return lf.with_columns(
        pl.lit(partitions["ano"]).cast(pl.Int32).alias("ano"),
        pl.lit(partitions["mes"]).cast(pl.Int32).alias("mes"),
    )


def _write_member(
    writer: LakeWriter,
    csv_path: Path,
    raw_file: Path,
    partitions: dict[str, int],
    key: str,
):
    """Escreve um membro; ``None`` se ele só tiver cabeçalho."""
    lf = _member_frame(csv_path, partitions)
    if lf is None:
        return None
    return writer.write_polars(
        lf, src=raw_file, partitions=partitions, file_key_name=key
    )


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
            if _is_auxiliary(raw_file.name):
                logger.info("transparencia-sp: %s e auxiliar; nao convertido", raw_file)
                res.skipped += 1
                continue
            period = _extract_year_month(raw_file.name)
            if period is None:
                res.errors.append(
                    f"{raw_file.name}: período (ano/mês) não inferível do nome "
                    "nem do carimbo; arquivo não convertido"
                )
                continue
            ano, mes = period
            partitions = {"ano": ano, "mes": mes}

            try:
                kind = _container_kind(raw_file)
                members = _member_names(raw_file, kind)
            except RarUnavailableError as exc:
                res.errors.append(f"{raw_file.name}: {exc}")
                continue
            except Exception as exc:
                res.errors.append(f"{raw_file.name}: arquivo ilegível: {exc}")
                continue

            for name in members:
                label = name or raw_file.name
                # Um arquivo de origem por membro: chave composta arquivo+membro.
                # Só com a chave do arquivo, o LakeWriter tomaria os membros
                # seguintes por já convertidos (mesmo sha256 e partição).
                key = composite_file_key(raw_file, name).lower()
                try:
                    if writer.is_current(
                        raw_file, partitions=partitions, file_key_name=key
                    ):
                        res.skipped += 1
                        continue
                    with _member_as_utf8(raw_file, kind, name) as csv_path:
                        try:
                            written = _write_member(
                                writer, csv_path, raw_file, partitions, key
                            )
                        except Exception as exc:
                            if not _is_ragged_error(exc):
                                raise
                            fixed = csv_path.with_name("membro-reparado.csv")
                            changed = repair_ragged_csv(csv_path, fixed)
                            logger.warning(
                                "transparencia-sp: %s: %d linha(s) com campos a mais; "
                                "excedente unido a ultima coluna",
                                label,
                                changed,
                            )
                            written = _write_member(
                                writer, fixed, raw_file, partitions, key
                            )
                        if written is None:
                            continue
                    if written.status == "skipped":
                        res.skipped += 1
                    else:
                        res.converted += 1
                except Exception as exc:
                    res.errors.append(
                        f"Erro ao converter {label} em {raw_file.name}: {exc}"
                    )

        return res


converter = TransparenciaSpLakeConverter()
