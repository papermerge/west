import yaml
import base64
import json
from pathlib import Path
from logging.config import dictConfig
from collections.abc import Mapping


def setup_logging(config: Path | None):
    if config is None:
        return

    with open(config, "r") as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)

    dictConfig(config)


def decode(s: str) -> Mapping:
    """Decodes given string from base64 to a python dictionary

    In other words it receives as argument a python
    string which base64 representation of a python
    dict, decode the base64 string and returns the
    dictionary.

    Example:

         'eyJ1c2VyX2lkIjogImExIn0=' -> {'user_id': 'a1'}

    In command line:

         > echo -n 'eyJ1c2VyX2lkIjogImExIn0=' | base64 -d
         > {"user_id": "a1"}
    """
    if not isinstance(s, str):
        raise ValueError("Input should be a string")

    if len(s) == 0:
        raise ValueError("Input should be non-empty string")

    rem = len(s) % 4

    if rem > 0:
        s += "=" * (4 - rem)

    json_str = base64.b64decode(s).decode()
    return json.loads(json_str)
