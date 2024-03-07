import click
import uvicorn

@click.group()
def cli():
    pass

@cli.command()
def start():
    """Starts the FastAPI application."""
    uvicorn.run("emilia.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == '__main__':
    cli()