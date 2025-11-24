import os
from typing import List
from dotenv import load_dotenv
from pathlib import Path

print(Path(__file__).resolve().parents[3]/".env")

load_dotenv(Path(__file__).resolve().parents[3]/".env")

class Settings():
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///news_database.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "1892dhianiandowqd0n")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "xxx")
    SENTRY_DSN: str = os.getenv(
        "SENTRY_DSN",
        "https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    )
    CORS_ORIGINS: List[str] = ["http://localhost:8080"]

settings = Settings()

# if not settings.OPENAI_API_KEY:
#     raise ValueError("嚴重錯誤: 未設定 OPENAI_API_KEY 環境變數！")

# if not settings.JWT_SECRET:
#     raise ValueError("嚴重錯誤: 未設定 JWT_SECRET 環境變數！")