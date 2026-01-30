from __future__ import annotations

import glob as globlib
import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from balloon_sim.config import AppConfig
from balloon_sim.meteo.decode import open_grib_any, summarize_datasets
from balloon_sim.meteo.fetch import Auth, DownloadError, download_to
from balloon_sim.meteo.run_locator import (
    GsmRun,
    build_open_gsm_1p25_upper_air_url,
    build_upper_air_global_url,
)
from balloon_sim.meteo.store import RawStore

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def version() -> None:
    """Print version."""
    typer.echo("balloon-sim-jma 0.0.0")


@app.command()
def doctor() -> None:
    """Sanity checks for dev install."""
    import balloon_sim

    typer.echo("OK: CLI is installed")
    typer.echo(f"balloon_sim module: {balloon_sim.__file__}")


@app.command()
def download_hr(
    run_id: str = typer.Option(..., help="UTC run id: YYYYMMDDHH (HH=00/06/12/18)"),
    grid: str = typer.Option("0.5", help="Grid degree: 0.5 or 0.25 (Closed / High-Res)"),
    fh: int = typer.Option(0, help="Forecast lead hours (FDddhh)"),
    out_dir: Path | None = typer.Option(None, help="Override data dir (default: data/)"),
    base_url: str | None = typer.Option(None, help="Override HR base URL (default from config/env)."),
    user: str | None = typer.Option(None, help="Auth user (or env JMA_WIS_USER)."),
    password: str | None = typer.Option(None, help="Auth password (or env JMA_WIS_PASSWORD)."),
    overwrite: bool = typer.Option(False, help="Overwrite existing file."),
    timeout_sec: int = typer.Option(300, help="HTTP timeout seconds."),
) -> None:
    """Download one Closed/High-Resolution GSM Upper_air (global) GRIB2 file."""
    cfg = AppConfig()
    base = base_url or cfg.jma_hr_gsm_base_url

    if len(run_id) != 10:
        raise typer.BadParameter("run_id must be YYYYMMDDHH (10 digits).")
    run = GsmRun(date_yyyymmdd=run_id[:8], cycle_hh=run_id[8:10])

    grid_deg = grid.strip()
    if grid_deg not in ("0.5", "0.25"):
        raise typer.BadParameter("grid must be 0.5 or 0.25")

    url = build_upper_air_global_url(base, grid_deg, run, fh)
    filename = url.split("/")[-1]

    store_root = out_dir or cfg.data_dir
    store = RawStore(store_root)
    dst = store.path_for_upper_air_global_hr(grid_deg, run, filename)

    u = user or cfg.jma_user
    p = password or cfg.jma_password
    auth = Auth(u, p) if (u and p) else None

    typer.echo(f"URL: {url}")
    typer.echo(f"OUT: {dst}")

    try:
        path = download_to(url, dst, auth=auth, overwrite=overwrite, timeout_sec=timeout_sec)
        typer.echo(f"Downloaded: {path} ({path.stat().st_size} bytes)")
    except DownloadError as e:
        typer.echo(f"Download failed: {e}")
        typer.echo("Hint: HR GSM is under 'Closed' and may require registration/valid credentials.")
        raise typer.Exit(code=1)


@app.command()
def download_open_gsm(
    run_id: str = typer.Option(..., help="UTC run id: YYYYMMDDHH (HH=00/06/12/18)"),
    fd_range: str = typer.Option(
        "FD0000-0512",
        help="Open 1.25deg file range: FD0000-0512 (0-132h) or FD0600-1100 (144-264h).",
    ),
    out_dir: Path | None = typer.Option(None, help="Override data dir (default: data/)"),
    base_url: str | None = typer.Option(None, help="Override OPEN base URL (default from config/env)."),
    overwrite: bool = typer.Option(False, help="Overwrite existing file."),
    timeout_sec: int = typer.Option(300, help="HTTP timeout seconds."),
) -> None:
    """Download Open deterministic global GSM (1.25 deg) upper-air GRIB2 file."""
    cfg = AppConfig()
    base = base_url or cfg.jma_open_grib_base_url

    if len(run_id) != 10:
        raise typer.BadParameter("run_id must be YYYYMMDDHH (10 digits).")
    run = GsmRun(date_yyyymmdd=run_id[:8], cycle_hh=run_id[8:10])

    if fd_range not in ("FD0000-0512", "FD0600-1100"):
        raise typer.BadParameter("fd_range must be FD0000-0512 or FD0600-1100")

    url = build_open_gsm_1p25_upper_air_url(base, run, fd_range=fd_range)
    filename = url.split("/")[-1]

    store_root = out_dir or cfg.data_dir
    store = RawStore(store_root)
    dst = store.path_for_open_gsm_1p25_upper_air(run, filename)

    typer.echo(f"URL: {url}")
    typer.echo(f"OUT: {dst}")

    path = download_to(url, dst, auth=None, overwrite=overwrite, timeout_sec=timeout_sec)
    typer.echo(f"Downloaded: {path} ({path.stat().st_size} bytes)")


@app.command()
def inspect_grib(
    paths: list[Path] = typer.Argument(
        None,
        help="GRIB2 file paths. You can pass multiple paths.",
    ),
    glob: str | None = typer.Option(
        None,
        "--glob",
        help="Glob pattern expanded by the CLI (recommended on PowerShell). Example: data\\raw\\...\\*.bin",
    ),
) -> None:
    """Inspect one or more GRIB2 files with cfgrib (prints JSON summaries)."""
    resolved: list[Path] = []

    if glob:
        resolved.extend([Path(s) for s in globlib.glob(glob)])

    if paths:
        resolved.extend(list(paths))

    # de-dup while preserving order
    seen: set[str] = set()
    uniq: list[Path] = []
    for rp in resolved:
        key = str(rp)
        if key not in seen:
            seen.add(key)
            uniq.append(rp)

    if not uniq:
        raise typer.BadParameter("No input files. Provide PATH(s) or --glob pattern.")

    results: dict[str, object] = {}
    for fp in uniq:
        try:
            if not fp.exists() or fp.is_dir():
                results[str(fp)] = {"error": "not a file"}
                continue
            dsets = open_grib_any(fp)
            results[str(fp)] = summarize_datasets(dsets)
        except Exception as e:
            results[str(fp)] = {"error": str(e)}

    typer.echo(json.dumps(results, indent=2, ensure_ascii=False))


@app.command()
def now_utc() -> None:
    """Print current UTC time (debug helper)."""
    typer.echo(datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    app()
