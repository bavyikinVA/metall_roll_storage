from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_SQLITE_URL: str = "sqlite+aiosqlite:///./test.db" # ниже установлены значения по умолчанию
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    # поля для postgresql
    API_KEY: str = ""
    PG_USER: str = ""
    PG_PASSWORD: str = ""
    PG_HOST: str = ""
    PG_PORT: int = 5432
    PG_NAME: str = ""

    def DB_URL(self):
        if self.DB_SQLITE_URL:
            return self.DB_SQLITE_URL
        else:
            return f"postgresql+psycopg2://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_NAME}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
print(f"Создана база данных из файла .env: {settings.DB_URL()}")