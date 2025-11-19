from apscheduler.schedulers.background import BackgroundScheduler
from src.services.news_service import NewsService
from src.utils.openai_client import OpenAIService
from src.db.session import SessionLocal

scheduler = BackgroundScheduler()

def _job_runner(openai_api_key):
    # create a fresh session for each run (important to avoid cross-thread sessions)
    db = SessionLocal()
    try:
        openai_client = OpenAIService(openai_api_key)
        NewsService(db, openai_client).assess_and_store()
    finally:
        db.close()

def schedule_news_job(settings, interval_minutes: int = 100):
    # add job if not present (keeps semantics of original scheduler.add_job)
    scheduler.add_job(lambda: _job_runner(settings.OPENAI_API_KEY), "interval", minutes=interval_minutes)
