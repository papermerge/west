import typer
from west.config import get_settings
import pprint

app = typer.Typer()

settings = get_settings()


@app.command(name="settings")
def print_settings():
    pprint.pprint(settings.model_dump())



if __name__ == "__main__":
    app()
