from pydantic.v1 import BaseSettings  # Импорт из pydantic.v1

class Settings(BaseSettings):
    database_url: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"

settings = Settings()