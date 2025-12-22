# import os
# from pathlib import Path
# from pydantic_settings import BaseSettings, SettingsConfigDict

# BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# # print(f"DEBUG: Looking for .env at: {os.path.join(BASE_DIR, '.env')}")

# class Settings(BaseSettings):
#     SECRET_KEY: str 
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

#     model_config = SettingsConfigDict(
#         env_file=os.path.join(BASE_DIR, ".env"),
#         env_ignore_empty=True,
#         extra="ignore"
#     )

# settings = Settings()

from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    SECRET_KEY: str

    model_config = {
        "env_file": ENV_FILE,
        "env_file_encoding": "utf-8",
    }

settings = Settings()

