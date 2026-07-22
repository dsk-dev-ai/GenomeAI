from __future__ import annotations

import typer
from genomeai_shared.constants import APP_NAME

from genomeai_cli.commands.doctor import doctor_cmd
from genomeai_cli.commands.version import version_cmd

app = typer.Typer(
    name=APP_NAME.lower(),
    help="GenomeAI command-line interface",
    no_args_is_help=True,
)

app.command(name="version")(version_cmd)
app.command(name="doctor")(doctor_cmd)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
