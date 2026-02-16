"""Rich terminal output: tables, banners, diagnostics."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from wfm.devices.registry import RegisteredDevice
from wfm.ssid.constants import INDEX_TO_BAND
from wfm.ssid.gate import APGateState, CompatibilityState
from wfm.ssid.mismatch import MismatchResult

console = Console()


def print_mismatch_banner() -> None:
    """Print a red warning banner for SSID mismatch."""
    console.print(
        Panel(
            "[bold white]Primary SSID mismatch detected. Cloud management paused.[/bold white]",
            style="bold red",
            title="BLOCKED",
            expand=False,
        )
    )


def print_diagnostic_table(result: MismatchResult, primary_indices: frozenset[int]) -> None:
    """Print a table showing index → band → SSID → status for each primary index."""
    table = Table(title="Primary SSID Diagnostic", show_lines=True)
    table.add_column("Index", justify="right", style="cyan")
    table.add_column("Band", style="magenta")
    table.add_column("SSID", style="white")
    table.add_column("Status", style="bold")

    for idx in sorted(primary_indices):
        band = INDEX_TO_BAND.get(idx, "?")
        ssid = result.index_to_ssid.get(idx, "—")

        if idx not in result.index_to_ssid:
            status = "[yellow]MISSING[/yellow]"
        elif result.has_collision:
            status = "[red]COLLISION[/red]"
        elif result.is_ok:
            status = "[green]OK[/green]"
        else:
            status = "[red]MISMATCH[/red]"

        table.add_row(str(idx), band, ssid, status)

    console.print(table)


def print_device_table(
    devices: list[RegisteredDevice],
    gate_states: dict[str, APGateState],
) -> None:
    """Print a summary table of all known APs."""
    table = Table(title="Access Points", show_lines=True)
    table.add_column("IP", style="cyan")
    table.add_column("Device ID", style="white")
    table.add_column("Type", style="magenta")
    table.add_column("Compatibility", style="bold")
    table.add_column("Blocked Since", style="yellow")
    table.add_column("Last Checked", style="dim")

    for dev in devices:
        gs = gate_states.get(dev.ip, APGateState())
        state = gs.compatibility_state

        if state == CompatibilityState.OK:
            compat = "[green]OK[/green]"
        elif state == CompatibilityState.PRIMARY_SSID_MISMATCH:
            compat = "[red]PRIMARY_SSID_MISMATCH[/red]"
        elif state == CompatibilityState.INDEX_COLLISION:
            compat = "[red]INDEX_COLLISION[/red]"
        else:
            compat = "[yellow]UNKNOWN[/yellow]"

        blocked_since = gs.detected_at if state != CompatibilityState.OK else ""
        last_checked = gs.last_checked_at

        table.add_row(
            dev.ip,
            dev.device_id,
            dev.profile.label,
            compat,
            blocked_since,
            last_checked,
        )

    console.print(table)


def print_status_ok(ip: str, primary_ssid: str) -> None:
    """Print a green status line for a passing AP."""
    console.print(f"  [green]✓[/green] {ip}: Primary SSID [bold]'{primary_ssid}'[/bold] — OK")


def print_status_fail(ip: str, details: str) -> None:
    """Print a red status line for a failing AP."""
    console.print(f"  [red]✗[/red] {ip}: {details}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[dim]{message}[/dim]")
