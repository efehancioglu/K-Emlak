from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url:str

    scraper_python_path: str
    scraper_script_path: str
    scraper_working_dir: str

    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8")

settings = Settings()