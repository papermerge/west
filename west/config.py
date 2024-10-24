from functools import lru_cache
from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings


class Algs(str, Enum):
    RS256 = "RS256"
    RS384 = "RS384"
    RS512 = "RS512"
    ES256 = "ES256"
    ES384 = "ES384"
    ES512 = "ES512"


class UserIDParamName(str, Enum):
    token = 'token'
    remote_user_id = 'remote-user-id'


class Settings(BaseSettings):
    papermerge__redis__url: str | None = None
    papermerge__main__logging_cfg: Path | None = Path("logging.yaml")
    user_id_param_name: UserIDParamName = UserIDParamName.token
    public_key: Path | None = None  # path to public key file; used to validate jwt tokens
    algorithms: list[Algs] = ['RS256']
    health_check_path: str = "/probe"


@lru_cache()
def get_settings():
    return Settings()
