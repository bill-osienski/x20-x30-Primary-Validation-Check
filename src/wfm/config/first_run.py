"""Interactive first-run setup and credential re-entry prompts."""

from __future__ import annotations

import click

from wfm.config.env_manager import EnvManager


def run_first_time_setup(env: EnvManager) -> None:
    """Prompt user for credentials and AP IPs, then encrypt and save."""
    click.echo("\n--- WFM Block - First-Time Setup ---\n")
    username = click.prompt("AP admin username")
    password = click.prompt("AP admin password", hide_input=True)
    raw_ips = click.prompt("AP IP address(es), comma-separated")
    ap_ips = [ip.strip() for ip in raw_ips.split(",") if ip.strip()]

    if not ap_ips:
        click.echo("Error: at least one AP IP is required.")
        raise SystemExit(1)

    env.set_credentials(username, password, ap_ips)
    env.save()
    click.echo(f"\nCredentials encrypted and saved to {env.env_path}")


def prompt_credential_reentry(env: EnvManager) -> bool:
    """After repeated auth failures, ask user to re-enter credentials.

    Returns True if credentials were updated, False if user declined.
    """
    click.echo("\nAuthentication failed after multiple retries.")
    if not click.confirm("Re-enter credentials?", default=True):
        return False

    username = click.prompt("AP admin username", default=env.username)
    password = click.prompt("AP admin password", hide_input=True)
    raw_ips = click.prompt("AP IP address(es), comma-separated", default=",".join(env.ap_ips))
    ap_ips = [ip.strip() for ip in raw_ips.split(",") if ip.strip()]

    env.set_credentials(username, password, ap_ips)
    env.save()
    click.echo("Credentials updated.")
    return True
