#!/usr/bin/env python
"""CLI commands for database and app management."""
import click
import os
from sqlalchemy import create_engine
from src.ghost_investor_ai.database import Base
from src.ghost_investor_ai.config import settings


@click.group()
def cli():
    """Ghost Investor AI CLI."""
    pass


@cli.command()
def db_init():
    """Initialize database schema."""
    click.echo("Initializing database...")
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    click.echo("✓ Database initialized successfully")


@cli.command()
def db_drop():
    """Drop all tables (use with caution!)."""
    if not click.confirm("Are you sure you want to drop all tables?"):
        click.echo("Cancelled.")
        return

    click.echo("Dropping all tables...")
    engine = create_engine(settings.database_url)
    Base.metadata.drop_all(bind=engine)
    click.echo("✓ All tables dropped")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to run on")
@click.option("--port", default=8000, type=int, help="Port to run on")
def run(host, port):
    """Run the development server."""
    import uvicorn

    click.echo(f"Starting server on {host}:{port}...")
    uvicorn.run(
        "src.ghost_investor_ai.main:app",
        host=host,
        port=port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    cli()
