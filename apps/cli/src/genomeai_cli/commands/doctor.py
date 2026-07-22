import platform
import sys

from rich.console import Console
from rich.table import Table


def doctor_cmd() -> None:
    table = Table(title="GenomeAI Environment")
    table.add_column("Check", style="cyan")
    table.add_column("Value", style="green")

    table.add_row(
        "Python",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )
    table.add_row("Platform", platform.platform())
    table.add_row("Architecture", platform.machine())

    console = Console()
    console.print(table)
