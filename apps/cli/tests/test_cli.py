from genomeai_cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "GenomeAI" in result.stdout


def test_doctor() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Environment" in result.stdout
    assert "Python" in result.stdout
    assert "Platform" in result.stdout
