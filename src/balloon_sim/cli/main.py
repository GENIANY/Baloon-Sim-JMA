from __future__ import annotations

import typer

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def version() -> None:
    """Print version."""
    typer.echo("balloon-sim-jma 0.0.0")


@app.command()
def doctor() -> None:
    """Sanity checks for dev install (placeholder)."""
    import balloon_sim
    typer.echo("OK: CLI is installed")
    typer.echo(f"balloon_sim module: {balloon_sim.__file__}")


if __name__ == "__main__":
    app()
