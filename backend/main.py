# main.py (修正版)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings  # 注意我們在 config.py 用 settings 實例
from src.core.logging_ import init_sentry
from src.db.session import SessionLocal, init_db
from src.workers.scheduler import scheduler, schedule_news_job
from src.services.news_service import NewsService
from src.utils.openai_client import OpenAIService

# routers
from src.api.v1 import news as news_router_module, users as users_router_module

# <-- 正確匯入 model（不要從 router 拿 model） -->
from src.models.news import NewsModel  # <- 這裡改為直接 import model

init_sentry(settings)

app = FastAPI()

# middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers (prefix 仍由 router 檔放路徑)
app.include_router(news_router_module.router, prefix="/api/v1/news")
app.include_router(users_router_module.router, prefix="/api/v1/users")

@app.on_event("startup")
def on_startup():
    # ensure DB tables exist
    init_db()

    # create a short-lived session to check if DB empty, same behavior as old main.py
    db = SessionLocal()
    try:
        # 使用真正的 model 去 query（不要從 router module 拿）
        news_count = db.query(NewsModel).count()
        if news_count == 0:
            try:
                openai_client = OpenAIService(settings.OPENAI_API_KEY)
                NewsService(db, openai_client).assess_and_store(is_initial=True)
            except Exception as exc:
                print("startup fetching error:", exc)
    finally:
        db.close()

    # schedule recurring job (use helper to ensure new session on each run)
    schedule_news_job(settings, interval_minutes=100)
    scheduler.start()

@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()
