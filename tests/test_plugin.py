"""Tests for transparencia-sp-fetcher Typer plugin."""

from typer.testing import CliRunner

from transparencia_sp_fetcher.plugin import app


def test_cli_list() -> None:
    """Test quantilica transparencia-sp list."""
    runner = CliRunner()
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "corrente" in result.output
    assert "historico" in result.output


def test_cli_convert_help() -> None:
    """Test quantilica transparencia-sp convert --help."""
    runner = CliRunner()
    result = runner.invoke(app, ["convert", "--help"])
    assert result.exit_code == 0
    assert "--lake" in result.output
