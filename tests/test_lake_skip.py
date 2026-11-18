"""O build do lake pula, sem ler o bruto, o que já está em dia."""

from __future__ import annotations

import builtins
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import pytest

import transparencia_sp_fetcher.lake as lake_mod
from transparencia_sp_fetcher.lake import converter

from .rar_fixture import make_rar4

CSV = (
    "Nome;Cargo;Orgao;Remuneracao Basica;Total Liquido\n"
    "FULANO;ANALISTA;FAZENDA;1.400,50;1.200,00\n"
    "BELTRANO;AUDITOR;FAZENDA;3.250,00;2.800,00\n"
)
SO_CABECALHO = "Nome;Cargo;Orgao;Remuneracao Basica;Total Liquido\n"


def _sidecar(path: Path) -> None:
    """Sidecar de manifesto confiável: o sha256 vem dele, sem ler o bruto."""
    data = path.read_bytes()
    path.with_name(path.name + ".manifest.json").write_text(
        json.dumps(
            {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
        ),
        encoding="utf-8",
    )


def _bruto(tmp_path: Path) -> Path:
    raw = tmp_path / "raw" / "remuneracao"
    raw.mkdir(parents=True)
    csv = raw / "remuneracao_2024-05@20261101.csv"
    csv.write_text(CSV, encoding="utf-8")
    _sidecar(csv)

    z = raw / "remuneracao_2024-06@20261101.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("a.csv", CSV.encode("utf-8-sig"))
        zf.writestr("b.csv", CSV.encode("utf-8-sig"))
        zf.writestr("vazio.csv", SO_CABECALHO.encode("utf-8-sig"))  # sem Parquet
    _sidecar(z)

    if _libarchive_ok():  # RAR só onde há leitor (libarchive)
        r = raw / "remuneracao_2013-01@20261101.rar"
        r.write_bytes(make_rar4([("2013.csv", CSV.encode("latin-1"))]))
        _sidecar(r)
    return tmp_path / "raw"


def _libarchive_ok() -> bool:
    try:
        lake_mod._libarchive()
    except lake_mod.RarUnavailableError:
        return False
    return True


@pytest.fixture
def acessos(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Registra todo acesso ao bruto: ZIP/RAR/7z, leitores e ``open``."""
    vistos: list[str] = []

    def espia(nome: str, original: Any) -> Any:
        def _f(*args: Any, **kwargs: Any) -> Any:
            vistos.append(nome)
            return original(*args, **kwargs)

        return _f

    monkeypatch.setattr(zipfile, "ZipFile", espia("ZipFile", zipfile.ZipFile))
    monkeypatch.setattr(subprocess, "run", espia("subprocess.run", subprocess.run))
    monkeypatch.setattr(subprocess, "Popen", espia("Popen", subprocess.Popen))
    for nome in (
        "_container_kind",
        "_member_names",
        "_member_chunks",
        "_member_as_utf8",
        "_libarchive",
    ):
        monkeypatch.setattr(lake_mod, nome, espia(nome, getattr(lake_mod, nome)))

    original_open = builtins.open

    def aberto(file: Any, *args: Any, **kwargs: Any) -> Any:
        if "raw" in Path(str(file)).parts and not str(file).endswith(".manifest.json"):
            vistos.append(f"open:{file}")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", aberto)
    monkeypatch.setattr(io, "open", aberto)
    return vistos


def test_segunda_rodada_nao_le_o_bruto(tmp_path: Path, acessos: list[str]) -> None:
    raw, lake = _bruto(tmp_path), tmp_path / "lake"
    res = converter.convert(raw, lake, datasets=["remuneracao"])
    assert not res.errors, res.errors
    # CSV solto (1) + 2 membros do ZIP (o de só cabeçalho não gera Parquet) + RAR (1)
    assert (res.converted, res.skipped) == (3 + (1 if _libarchive_ok() else 0), 0)
    convertidos = res.converted
    assert acessos

    acessos.clear()
    res2 = converter.convert(raw, lake, datasets=["remuneracao"])
    assert (res2.converted, res2.errors) == (0, [])
    assert res2.skipped == convertidos
    assert acessos == []


def test_force_le_o_bruto_e_reconverte(tmp_path: Path, acessos: list[str]) -> None:
    raw, lake = _bruto(tmp_path), tmp_path / "lake"
    primeira = converter.convert(raw, lake, datasets=["remuneracao"])
    acessos.clear()
    res = converter.convert(raw, lake, datasets=["remuneracao"], force=True)
    assert (res.converted, res.skipped) == (primeira.converted, 0)
    assert "_container_kind" in acessos and "ZipFile" in acessos


def test_bruto_novo_converte_e_os_antigos_nao_sao_lidos(
    tmp_path: Path, acessos: list[str]
) -> None:
    raw, lake = _bruto(tmp_path), tmp_path / "lake"
    primeira = converter.convert(raw, lake, datasets=["remuneracao"])
    novo = raw / "remuneracao" / "remuneracao_2024-07@20261201.csv"
    novo.write_text(CSV, encoding="utf-8")
    _sidecar(novo)

    acessos.clear()
    res = converter.convert(raw, lake, datasets=["remuneracao"])
    assert (res.converted, res.skipped, res.errors) == (1, primeira.converted, [])
    assert acessos
    assert all("2024-05" not in a and "2024-06" not in a for a in acessos)


def test_zip_alterado_reconverte(tmp_path: Path, acessos: list[str]) -> None:
    raw, lake = _bruto(tmp_path), tmp_path / "lake"
    converter.convert(raw, lake, datasets=["remuneracao"])
    z = raw / "remuneracao" / "remuneracao_2024-06@20261101.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("a.csv", (CSV + "NOVO;X;Y;1,00;1,00\n").encode("utf-8-sig"))
    _sidecar(z)

    acessos.clear()
    res = converter.convert(raw, lake, datasets=["remuneracao"])
    # a (mudou) converte; b é só chave composta do ZIP antigo e fica órfã no lake
    assert res.errors == []
    assert res.converted >= 1
    assert "ZipFile" in acessos


def test_arquivo_sem_parquet_continua_sendo_reexaminado(
    tmp_path: Path, acessos: list[str]
) -> None:
    """ZIP só com membro de cabeçalho não deixa Parquet: segue sendo aberto."""
    raw = tmp_path / "raw" / "remuneracao"
    raw.mkdir(parents=True)
    z = raw / "remuneracao_2024-06@20261101.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("vazio.csv", SO_CABECALHO.encode("utf-8-sig"))
    _sidecar(z)
    lake = tmp_path / "lake"
    for _ in range(2):
        acessos.clear()
        res = converter.convert(raw.parent, lake, datasets=["remuneracao"])
        assert (res.converted, res.skipped, res.errors) == (0, 0, [])
        assert "ZipFile" in acessos
