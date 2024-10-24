import logging
import yaml
import base64
import json
from pathlib import Path
from logging.config import dictConfig
from collections.abc import Mapping
from west.config import get_settings
import jwt

logger = logging.getLogger(__name__)
settings = get_settings()

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

try:
    public_cert = open(settings.public_key, 'r').read()
except Exception:
    public_cert = None


def token_is_valid(token: str) -> bool:
    if public_cert is None:
        logger.error(f"Missing public key certificate: {settings.public_key}")
        return False

    try:
        jwt.decode(
            token,
            public_cert,
            algorithms=settings.algorithms,
            options={
                'verify_aud': False,
                'verify_iss': False,
                'verify_sub': False,
                'verify_jti': False,
            }
        )
    except Exception as e:
        logger.debug(e)
        return False

    return True
