"""Click CLI commands: status, recheck, setup."""

from __future__ import annotations

from pathlib import Path

import click

from wfm.api.client import DEFAULT_HTTP_PORT, DEFAULT_HTTPS_PORT, APClient
from wfm.api.endpoints import APEndpoints
from wfm.api.exceptions import (
    DeviceDetectionError,
    TokenRefreshExhaustedError,
)
from wfm.auth.login import LoginService
from wfm.auth.token_manager import TokenManager
from wfm.config.crypto import CryptoEngine
from wfm.config.env_manager import EnvManager
from wfm.config.first_run import prompt_credential_reentry, run_first_time_setup
from wfm.devices.detector import detect_device_type
from wfm.devices.registry import DeviceRegistry
from wfm.display.formatters import (
    console,
    print_device_table,
    print_diagnostic_table,
    print_error,
    print_info,
    print_mismatch_banner,
    print_status_fail,
    print_status_ok,
)
from wfm.ssid.gate import CompatibilityGate, CompatibilityState
from wfm.ssid.mismatch import check_primary_ssid_mismatch

PROJECT_DIR = Path.cwd()
ENV_PATH = PROJECT_DIR / ".env"
KEY_PATH = PROJECT_DIR / ".env.key"
STATE_PATH = PROJECT_DIR / ".wfm_state.json"


class AppContext:
    """Shared application state passed through Click context."""

    def __init__(
        self,
        env: EnvManager,
        login_service: LoginService,
        token_manager: TokenManager,
        gate: CompatibilityGate,
        registry: DeviceRegistry,
        insecure: bool,
        port: int,
        scheme: str,
    ) -> None:
        self.env = env
        self.login_service = login_service
        self.token_manager = token_manager
        self.gate = gate
        self.registry = registry
        self.insecure = insecure
        self.port = port
        self.scheme = scheme

    def make_client(self, ip: str) -> APClient:
        return APClient(
            ip,
            port=self.port,
            scheme=self.scheme,
            verify=not self.insecure,
        )


def _init_app(insecure: bool, port: int | None, http: bool) -> AppContext:
    """Initialize crypto, env, auth, and gate."""
    crypto = CryptoEngine(KEY_PATH)
    env = EnvManager(ENV_PATH, crypto)
    env.load()

    if not env.is_configured():
        run_first_time_setup(env)
        env.load()

    scheme = "http" if http else "https"
    effective_port = port or (DEFAULT_HTTP_PORT if http else DEFAULT_HTTPS_PORT)

    login_service = LoginService(env.username, env.password)
    token_manager = TokenManager(login_service)
    gate = CompatibilityGate(STATE_PATH)
    registry = DeviceRegistry()

    return AppContext(
        env=env,
        login_service=login_service,
        token_manager=token_manager,
        gate=gate,
        registry=registry,
        insecure=insecure,
        port=effective_port,
        scheme=scheme,
    )


def _detect_and_check(
    app: AppContext,
    ip: str,
    endpoints: APEndpoints,
) -> None:
    """Detect device type and run mismatch check for a single AP."""
    # Detect device type
    radiostatus = endpoints.get_radiostatus()
    profile = detect_device_type(ip, radiostatus)

    # Get device ID from token state
    token_state = app.token_manager.get_state(ip)
    device_id = token_state.device_id if token_state else ""
    app.registry.register(ip, device_id, profile)

    # Get networks and run mismatch check
    networks_resp = endpoints.get_networks()
    result = check_primary_ssid_mismatch(networks_resp.Networks, profile)

    # Update gate state
    if result.is_ok:
        app.gate.update_state(
            ip,
            state=CompatibilityState.OK,
            primary_ssid=result.primary_ssid or "",
            index_to_ssid=result.index_to_ssid,
        )
        print_status_ok(ip, result.primary_ssid or "")
    elif result.has_collision:
        app.gate.update_state(
            ip,
            state=CompatibilityState.INDEX_COLLISION,
            details=result.details,
            index_to_ssid=result.index_to_ssid,
        )
        print_status_fail(ip, result.details)
        print_diagnostic_table(result, profile.primary_indices)
    else:
        app.gate.update_state(
            ip,
            state=CompatibilityState.PRIMARY_SSID_MISMATCH,
            details=result.details,
            index_to_ssid=result.index_to_ssid,
        )
        print_status_fail(ip, result.details)
        print_diagnostic_table(result, profile.primary_indices)


def _auth_and_check(app: AppContext, ip: str) -> None:
    """Authenticate with an AP, then detect and check."""
    client = app.make_client(ip)
    endpoints = APEndpoints(client)
    try:
        app.token_manager.ensure_token(ip, endpoints)
        _detect_and_check(app, ip, endpoints)
    except TokenRefreshExhaustedError:
        if prompt_credential_reentry(app.env):
            app.login_service.update_credentials(app.env.username, app.env.password)
            try:
                app.token_manager.authenticate(ip, endpoints)
                _detect_and_check(app, ip, endpoints)
            except TokenRefreshExhaustedError:
                print_error(f"Authentication still failing for {ip}. Check credentials.")
        else:
            print_error(f"Cannot authenticate with {ip}.")
    except DeviceDetectionError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"{ip}: {e}")
    finally:
        client.close()


@click.group()
@click.option("--insecure/--secure", default=True, help="TLS certificate verification (default: insecure)")
@click.option("--port", type=int, default=None, help="Override default port")
@click.option("--http", is_flag=True, help="Use HTTP instead of HTTPS")
@click.pass_context
def cli(ctx: click.Context, insecure: bool, port: int | None, http: bool) -> None:
    """WFM Block — SnapOne Access Point management CLI."""
    ctx.ensure_object(dict)
    ctx.obj["insecure"] = insecure
    ctx.obj["port"] = port
    ctx.obj["http"] = http


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show all APs: type, compatibility state, diagnostics."""
    app = _init_app(ctx.obj["insecure"], ctx.obj["port"], ctx.obj["http"])

    has_mismatch = False
    for ip in app.env.ap_ips:
        _auth_and_check(app, ip)
        gs = app.gate.get_state(ip)
        if gs.compatibility_state != CompatibilityState.OK:
            has_mismatch = True

    console.print()
    if has_mismatch:
        print_mismatch_banner()
        console.print()

    print_device_table(app.registry.all_devices(), app.gate.all_states)


@cli.command()
@click.argument("ip", required=False)
@click.pass_context
def recheck(ctx: click.Context, ip: str | None) -> None:
    """Re-run SSID mismatch check on one or all APs."""
    app = _init_app(ctx.obj["insecure"], ctx.obj["port"], ctx.obj["http"])

    targets = [ip] if ip else app.env.ap_ips
    print_info(f"Rechecking {len(targets)} AP(s)...")
    console.print()

    for target_ip in targets:
        _auth_and_check(app, target_ip)

    console.print()
    # Show summary
    all_ok = all(
        app.gate.get_state(t).compatibility_state == CompatibilityState.OK for t in targets
    )
    if all_ok:
        console.print("[green]All checked APs passed.[/green]")
    else:
        print_mismatch_banner()


@cli.command()
def setup() -> None:
    """Re-run credential & IP setup."""
    crypto = CryptoEngine(KEY_PATH)
    env = EnvManager(ENV_PATH, crypto)
    env.load()
    run_first_time_setup(env)
    console.print("[green]Setup complete.[/green]")
