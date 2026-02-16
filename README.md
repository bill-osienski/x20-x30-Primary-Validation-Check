# x20/x30 Primary Validation Check

CLI tool for validating primary SSID configuration across SnapOne x20 (Wi-Fi 6) and x30 (Wi-Fi 7) access points.

## What It Does

Before any SSID sync or import operation, this tool checks that every AP's primary network indices share the same SSID name. If they don't, destructive operations are blocked until the mismatch is resolved.

- **x20 (Wi-Fi 6):** Validates indices `0` (2.4 GHz) and `50` (5 GHz)
- **x30 (Wi-Fi 7):** Validates indices `0` (2.4 GHz), `50` (5 GHz), and `70` (6 GHz)

The tool auto-detects device type via the `radiostatus` API response shape (2 radios = x20, 3 radios = x30).

## Requirements

- Python 3.14.2+
- Network access to your SnapOne access points

## Installation

```bash
# Clone the repo
git clone git@github.com:bill-osienski/x20-x30-Primary-Validation-Check.git
cd x20-x30-Primary-Validation-Check

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with all dependencies
pip install .

# Or include dev dependencies (pytest, ruff, mypy)
pip install .[dev]
```

## First-Run Setup

On first run, the CLI will prompt you interactively for:

1. **AP admin username**
2. **AP admin password**
3. **AP IP addresses** (comma-separated)

Credentials are encrypted with Fernet (via `cryptography`) and stored in `.env`. The encryption key is stored in `.env.key`. Both files are gitignored.

You can also copy `.env.template` to `.env` and fill in values manually before running.

## Usage

```bash
# Show status of all configured APs (type, compatibility state, diagnostics)
wfm status

# Re-run the SSID mismatch check on all APs
wfm recheck

# Re-run the check on a single AP
wfm recheck 192.168.1.100

# Re-run credential and IP setup
wfm setup
```

### Global Options

| Flag | Description |
|---|---|
| `--insecure` / `--secure` | Toggle TLS certificate verification (default: insecure) |
| `--port PORT` | Override the default port |
| `--http` | Use HTTP instead of HTTPS |

Example:

```bash
wfm --secure --port 8443 status
```

## How the Validation Works

1. Authenticate with each AP and obtain a JWT token
2. Query `radiostatus` to auto-detect x20 vs x30
3. Query `networks` to get all WLAN entries
4. Build a map of SSID name to network indices
5. Check that all primary indices resolve to the **same** SSID:
   - **PASS** — one SSID covers all primary indices
   - **INDEX COLLISION** — a primary index is claimed by multiple SSIDs
   - **PRIMARY SSID MISMATCH** — different SSIDs on different primary indices

When a mismatch or collision is detected, gated operations (`import_ssids`, `sync_ssids`, `apply_ssid_changes`, `push_ssid`, `reconcile`) are blocked until resolved.

## Project Structure

```
src/wfm/
  api/          # HTTP client, endpoint wrappers, models, exceptions
  auth/         # JWT login service and token manager
  config/       # Encrypted env management, first-run setup, crypto
  devices/      # Device type detection, profiles, registry
  display/      # Rich console formatters and tables
  ssid/         # Mismatch detection algorithm, constants, gate
  cli.py        # Click CLI commands (status, recheck, setup)
tests/          # pytest test suite
API_Docs/       # OpenAPI specs for x20 and x30
```

## Running Tests

```bash
pytest
```

## Linting and Type Checking

```bash
ruff check src tests
mypy src
```
