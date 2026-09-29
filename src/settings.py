from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    POSTGRES_CONNECTION_STRING: str
    CAPASHINO_URL: str
    CAPASHINO_API_TOKEN: str

    @property
    def async_database_url(self) -> str:
        for prefix in ("postgresql://", "postgres://"):
            if self.POSTGRES_CONNECTION_STRING.startswith(prefix):
                return (
                    "postgresql+asyncpg://"
                    + self.POSTGRES_CONNECTION_STRING.removeprefix(prefix)
                )
        return self.POSTGRES_CONNECTION_STRING
