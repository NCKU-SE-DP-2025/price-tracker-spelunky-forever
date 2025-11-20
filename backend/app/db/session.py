from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

# create engine and SessionLocal (same semantics as previous DBManager.create_engine)
engine = create_engine(settings.DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # ensure tables exist (same as Base.metadata.create_all in original DBManager)
    Base.metadata.create_all(bind=engine)

# dependency for FastAPI endpoints
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()