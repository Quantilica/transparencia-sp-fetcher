"""Série antiga (RAR) e períodos do lake de transparencia-sp."""

from __future__ import annotations

import io
import subprocess
import sys
import types
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
    monkeypatch.delenv("QUANTILICA_7Z", raising=False)
    monkeypatch.setattr(lake.shutil, "which", lambda exe: None)
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


# --- 7-Zip como alternativa à libarchive -----------------------------------------

# Saída de `7z l -slt -ba -sccUTF-8` (7-Zip 23/24) de um RAR: pasta, CSV e TXT.
SLT_LISTING = """\
Path = docs
Folder = +
Size = 0
Packed Size = 0
Modified = 2012-07-05 10:11:12
Attributes = D
CRC =
Encrypted = -
Method = m0
Host OS = Windows
Version = 29
Volume Index = 0

Path = docs\\remuneracao_Junho_2012.csv
Folder = -
Size = {csv_size}
Packed Size = {csv_size}
Modified = 2012-07-05 10:11:12
Attributes = A
CRC = 1A2B3C4D
Encrypted = -
Method = m3
Host OS = Windows
Version = 29
Volume Index = 0

Path = outra_parte.txt
Folder = -
Size = {txt_size}
Packed Size = {txt_size}
Modified = 2012-07-05 10:11:12
Attributes = A
CRC = 5E6F7A8B
Encrypted = -
Method = m3
Host OS = Windows
Version = 29
Volume Index = 0

Path = LEIAME.pdf
Folder = -
Size = 4
Packed Size = 4
Attributes = A
"""

CSV_NAME = "docs\\remuneracao_Junho_2012.csv"
TXT_NAME = "outra_parte.txt"


class FakeSevenZip:
    """Imita o 7z: `l` devolve o -slt; `e -so` devolve os bytes do membro."""

    def __init__(
        self, members: dict[str, bytes], rc: int = 0, stderr: str = ""
    ) -> None:
        self.members = members
        self.rc = rc
        self.stderr = stderr
        self.calls: list[list[str]] = []

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(lake, "_libarchive", _no_libarchive)
        monkeypatch.delenv("QUANTILICA_7Z", raising=False)
        monkeypatch.setattr(lake.shutil, "which", lambda exe: "/fake/7z")
        monkeypatch.setattr(lake.subprocess, "run", self.run)
        monkeypatch.setattr(lake.subprocess, "Popen", self.popen)

    def run(self, args, **kw):
        self.calls.append(list(args))
        assert isinstance(args, list) and kw.get("shell") is None
        listing = SLT_LISTING.format(
            csv_size=len(self.members[CSV_NAME]), txt_size=len(self.members[TXT_NAME])
        )
        out = b"" if self.rc else listing.encode("utf-8")
        return subprocess.CompletedProcess(
            args, self.rc, out, self.stderr.encode("utf-8")
        )

    def popen(self, args, stdout=None, stderr=None, **kw):
        self.calls.append(list(args))
        assert isinstance(args, list) and args[:3] == ["/fake/7z", "e", "-so"]
        name = args[-1]
        if self.rc:
            stderr.write(self.stderr.encode("utf-8"))
        fake = types.SimpleNamespace()
        fake.stdout = io.BytesIO(b"" if self.rc else self.members[name])
        fake.wait = lambda: self.rc
        return fake


def _no_libarchive():
    raise RarUnavailableError("libarchive ausente")


def _fake_rar(raw: Path, ym: str = "2012-06") -> Path:
    path = raw / f"remuneracao_rar_{ym}@20261101.rar"
    path.write_bytes(b"Rar!\x1a\x07\x00" + b"\x00" * 32)
    return path


def test_rar_via_7zip_converte_ate_parquet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw, lk, ds = _lake(tmp_path)
    _fake_rar(raw)
    fake = FakeSevenZip(
        {CSV_NAME: CSV_2013, TXT_NAME: CSV_2013.replace(b"JO\xc3O", b"JOSE")}
    )
    fake.install(monkeypatch)
    res = converter.convert(raw.parent, lk)
    assert not res.errors, res.errors
    assert res.converted == 2  # pasta e PDF ignorados
    assert not check_dataset(ds)
    df = pl.read_parquet(list((ds / "ano=2012" / "mes=6").glob("*.parquet")))
    assert df.height == 4
    assert "JOÃO DA SILVA" in df["nome"].to_list()
    assert df["totmes_final"][0] == 1400.50
    listing, *extractions = fake.calls
    assert listing[1:5] == ["l", "-slt", "-ba", "-sccUTF-8"]
    assert [c[-1] for c in extractions] == [CSV_NAME, TXT_NAME]
    assert all("-so" in c and "-spd" in c for c in extractions)
    # reconversão: nada novo
    res2 = converter.convert(raw.parent, lk)
    assert (res2.converted, res2.skipped, res2.errors) == (0, 2, [])


def test_rar_7zip_codigo_de_saida_nao_zero_vira_erro(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw, lk, ds = _lake(tmp_path)
    rar = _fake_rar(raw)
    fake = FakeSevenZip({CSV_NAME: CSV_2013, TXT_NAME: CSV_2013})
    fake.install(monkeypatch)
    assert lake._member_names(rar, "rar") == [CSV_NAME, TXT_NAME]
    fake.rc, fake.stderr = 2, "ERROR: Data Error in 'x.csv'. File is broken"
    with pytest.raises(RuntimeError, match="Data Error"):
        b"".join(lake._member_chunks(rar, "rar", CSV_NAME))
    # no conversor o erro é contado, sem nada gravado
    res = converter.convert(raw.parent, lk)
    assert res.converted == 0 and len(res.errors) == 1
    assert "Data Error" in res.errors[0]
    assert not ds.exists() or not list(ds.rglob("*.parquet"))


@pytest.mark.parametrize(
    "msg",
    [
        "ERROR: f.rar : Cannot open the file as archive",
        "ERROR: Can not open the file as archive",
        "Unsupported archive type",
    ],
)
def test_rar_7zip_sem_codec_rar_erro_cita_as_duas_saidas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, msg: str
) -> None:
    raw, lk, _ = _lake(tmp_path)
    _fake_rar(raw)
    FakeSevenZip({CSV_NAME: b"", TXT_NAME: b""}, rc=2, stderr=msg).install(monkeypatch)
    res = converter.convert(raw.parent, lk)
    assert res.converted == 0 and len(res.errors) == 1
    err = res.errors[0]
    assert "libarchive" in err and "7-Zip" in err and "codec RAR" in err


def test_rar_sem_libarchive_nem_7zip_cita_as_duas_saidas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw, lk, _ = _lake(tmp_path)
    _fake_rar(raw)
    monkeypatch.setitem(sys.modules, "libarchive", None)  # import falha de verdade
    monkeypatch.delenv("QUANTILICA_7Z", raising=False)
    monkeypatch.delenv("ProgramFiles", raising=False)
    monkeypatch.delenv("ProgramW6432", raising=False)
    monkeypatch.setattr(lake.shutil, "which", lambda exe: None)
    res = converter.convert(raw.parent, lk)
    assert res.converted == 0 and len(res.errors) == 1
    assert "libarchive" in res.errors[0] and "7-Zip" in res.errors[0]


def test_quantilica_7z_sobrescreve_o_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUANTILICA_7Z", "/opt/7zip/7zz")
    monkeypatch.setattr(lake.shutil, "which", lambda exe: "/usr/bin/7z")
    assert lake._sevenzip() == "/opt/7zip/7zz"


def test_libarchive_continua_sendo_a_primeira_opcao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = object()
    monkeypatch.setattr(lake, "_libarchive", lambda: sentinel)

    def nao_deve_chamar(*a, **k):
        raise AssertionError("7z não deveria ser usado com libarchive presente")

    monkeypatch.setattr(lake, "_sevenzip", nao_deve_chamar)
    assert lake._rar_backend() == ("libarchive", sentinel)


@needs_rar
def test_libarchive_presente_nao_chama_7zip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw, lk, _ = _lake(tmp_path)
    (raw / "remuneracao_rar_2013-02@20261101.rar").write_bytes(
        make_rar4([("a.txt", CSV_2013)])
    )

    def nao_deve_chamar(*a, **k):
        raise AssertionError("7z não deveria ser usado com libarchive presente")

    monkeypatch.setattr(lake.subprocess, "run", nao_deve_chamar)
    monkeypatch.setattr(lake.subprocess, "Popen", nao_deve_chamar)
    res = converter.convert(raw.parent, lk)
    assert res.converted == 1 and not res.errors


def test_rar_7zip_membro_ausente_vira_erro(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw, _, _ = _lake(tmp_path)
    rar = _fake_rar(raw)
    FakeSevenZip({CSV_NAME: CSV_2013, TXT_NAME: b"", "x": b""}).install(monkeypatch)
    with pytest.raises(FileNotFoundError):
        b"".join(lake._member_chunks(rar, "rar", "x"))
