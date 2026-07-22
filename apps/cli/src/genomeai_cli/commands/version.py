import typer
from genomeai_shared.constants import APP_NAME, VERSION


def version_cmd() -> None:
    typer.echo(f"{APP_NAME} v{VERSION}")
