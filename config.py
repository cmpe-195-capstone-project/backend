from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# NOTE: if this doesn't work switch to the dotenv lib
class Settings(BaseSettings):
    API_URL: str
    DATABASE_URL: str

    # tells Pydantic to load the variables from a file named '.env'
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()

# sinngle instance to import into other files
settings = get_settings()
