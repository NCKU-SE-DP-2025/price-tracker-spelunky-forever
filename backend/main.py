# ===== 標準庫 =====
import json
import os
import itertools
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import quote

# ===== 第三方 =====
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from openai import OpenAI
from pydantic import BaseModel, Field, AnyHttpUrl
import requests
from bs4 import BeautifulSoup
from jose import JWTError, jwt
from passlib.context import CryptContext

# ===== SQLAlchemy =====
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, relationship

# ===== 初始化 ORM base =====n
Base = declarative_base()

# Configuration
DB_URL = os.getenv("DATABASE_URL", "sqlite:///news_database.db")
SECRET_KEY = os.getenv("JWT_SECRET", "1892dhianiandowqd0n")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "xxx")

# Association table & models
user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )

class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )

# Database manager (single place to create sessions)
class DBManager:
    def __init__(self, db_url: str = DB_URL):
        self.engine = create_engine(db_url, echo=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        # ensure tables
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.SessionLocal()


# instantiate DB manager
db_manager = DBManager()

# OpenAI wrapper (centralize and add basic error handling)
class OpenAIService:
    def __init__(self, api_key: str = OPENAI_API_KEY):
        self.client = OpenAI(api_key=api_key)

    def chat(self, messages: List[dict], model: str = "gpt-3.5-turbo") -> str:
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return completion.choices[0].message.content
        except Exception as exc:
            # In production, log to sentry or logger
            print("OpenAI error:", exc)
            return ""

openai_service = OpenAIService()

# Scraper utility
class Scraper:
    @staticmethod
    def fetch_article_details(url: str) -> dict:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("h1", class_="article-content__title")
        time_tag = soup.find("time", class_="article-content__time")
        content_section = soup.find("section", class_="article-content__editor")

        title = title_tag.text if title_tag else ""
        time = time_tag.text if time_tag else ""
        paragraphs = []
        if content_section:
            paragraphs = [
                p.text
                for p in content_section.find_all("p")
                if p.text.strip() != "" and "▪" not in p.text
            ]
        return {"title": title, "time": time, "content": paragraphs}

# Repositories (DB access logic grouped)
class NewsRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_article(self, news_data: dict):
        # avoid duplicates by url
        existing = self.db.query(NewsArticle).filter_by(url=news_data["url"]).first()
        if existing:
            return existing
        article = NewsArticle(
            url=news_data["url"],
            title=news_data["title"],
            time=news_data["time"],
            content=news_data["content"] if isinstance(news_data["content"], str) else " ".join(news_data["content"]),
            summary=news_data.get("summary", ""),
            reason=news_data.get("reason", ""),
        )
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def list_all(self):
        return self.db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()

    def exists(self, article_id: int):
        return self.db.query(NewsArticle).filter_by(id=article_id).first() is not None

    def get_upvote_count(self, article_id: int):
        return (
            self.db.query(user_news_association_table)
            .filter_by(news_articles_id=article_id)
            .count()
        )

    def user_has_upvoted(self, article_id: int, user_id: int):
        return (
            self.db.query(user_news_association_table)
            .filter_by(news_articles_id=article_id, user_id=user_id)
            .first()
            is not None
        )

    def toggle_upvote(self, article_id: int, user_id: int):
        existing = (
            self.db.query(user_news_association_table)
            .filter_by(news_articles_id=article_id, user_id=user_id)
            .first()
        )
        if existing:
            delete_stmt = delete(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == article_id,
                user_news_association_table.c.user_id == user_id,
            )
            self.db.execute(delete_stmt)
            self.db.commit()
            return "Upvote removed"
        else:
            insert_stmt = insert(user_news_association_table).values(
                news_articles_id=article_id, user_id=user_id
            )
            self.db.execute(insert_stmt)
            self.db.commit()
            return "Article upvoted"


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, username: str, hashed_password: str):
        user = User(username=username, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

# Services (business logic grouped)
class NewsService:
    def __init__(self, db: Session, openai_client: OpenAIService):
        self.db = db
        self.openai = openai_client
        self.repo = NewsRepository(db)

    @staticmethod
    def fetch_news_info(search_term, is_initial=False):
        all_news_data = []
        if is_initial:
            pages_batches = []
            for page in range(1, 10):
                page_params = {
                    "page": page,
                    "id": f"search:{quote(search_term)}",
                    "channelId": 2,
                    "type": "searchword",
                }
                response = requests.get("https://udn.com/api/more", params=page_params, timeout=10)
                pages_batches.append(response.json().get("lists", []))

            for batch in pages_batches:
                all_news_data.extend(batch)
        else:
            page_params = {
                "page": 1,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=page_params, timeout=10)
            all_news_data = response.json().get("lists", [])
        return all_news_data

    def assess_and_store(self, is_initial=False):
        news_data = self.fetch_news_info("價格", is_initial=is_initial)
        for news_item in news_data:
            article_title = news_item.get("title", "")
            relevance_messages = [
                {
                    "role": "system",
                    "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
                },
                {"role": "user", "content": f"{article_title}"},
            ]
            relevance = self.openai.chat(relevance_messages)
            if relevance.strip().lower() == "high":
                try:
                    details = Scraper.fetch_article_details(news_item.get("titleLink", ""))
                    detailed_news = {
                        "url": news_item.get("titleLink", ""),
                        "title": details.get("title", ""),
                        "time": details.get("time", ""),
                        "content": details.get("content", []),
                    }
                    summary_messages = [
                        {
                            "role": "system",
                            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                        },
                        {"role": "user", "content": " ".join(detailed_news["content"])},
                    ]
                    result_text = self.openai.chat(summary_messages)
                    try:
                        result = json.loads(result_text)
                        detailed_news["summary"] = result.get("影響", "")
                        detailed_news["reason"] = result.get("原因", "")
                    except Exception:
                        detailed_news["summary"] = ""
                        detailed_news["reason"] = ""

                    self.repo.save_article(detailed_news)
                except Exception as exc:
                    print("error fetching/storing article:", exc)


class AuthService:
    def __init__(self, db: Session, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM):
        self.db = db
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.user_repo = UserRepository(db)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def authenticate_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = self.user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

# FastAPI app wiring (endpoints largely preserved)
app = FastAPI()
scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

ARTICLE_ID_COUNTER = itertools.count(start=1000000)

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", "https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000"),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

# dependency to get DB session
def get_db_session():
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

# helper to serialize article without internal SA state
def article_to_dict(article: NewsArticle):
    return {
        "id": article.id,
        "url": article.url,
        "title": article.title,
        "time": article.time,
        "content": article.content,
        "summary": article.summary,
        "reason": article.reason,
    }

# Startup / shutdown - keep behavior but add basic error handling
@app.on_event("startup")
def start_scheduler():
    db = db_manager.get_session()
    try:
        if db.query(NewsArticle).count() == 0:
            try:
                NewsService(db, openai_service).assess_and_store(is_initial=True)
            except Exception as exc:
                print("startup fetching error:", exc)
    finally:
        db.close()

    scheduler.add_job(lambda: NewsService(db_manager.get_session(), openai_service).assess_and_store(), "interval", minutes=100)
    scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

# Auth helpers that use AuthService
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user_if_password_correct(db: Session, username: str, password: str):
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def authenticate_user_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db_session)):
    auth_service = AuthService(db)
    return auth_service.authenticate_token(token)

# Endpoints
@app.post("/api/v1/users/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db_session)
):
    user = get_user_if_password_correct(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    auth_service = AuthService(db)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

class UserAuthSchema(BaseModel):
    username: str
    password: str

@app.post("/api/v1/users/register")
def create_user(user: UserAuthSchema, db: Session = Depends(get_db_session)):
    hashed_password = pwd_context.hash(user.password)
    user_repo = UserRepository(db)
    db_user = user_repo.create_user(user.username, hashed_password)
    return {"id": db_user.id, "username": db_user.username}

@app.get("/api/v1/users/me")
def read_users_me(current_user=Depends(authenticate_user_token)):
    return {"username": current_user.username}

# News endpoints
@app.get("/api/v1/news/news")
def read_news(db: Session = Depends(get_db_session)):
    repo = NewsRepository(db)
    news = repo.list_all()
    result = []
    for n in news:
        upvotes = repo.get_upvote_count(n.id)
        result.append({**article_to_dict(n), "upvotes": upvotes, "is_upvoted": False})
    return result

@app.get("/api/v1/news/user_news")
def read_user_news(db: Session = Depends(get_db_session), current_user=Depends(authenticate_user_token)):
    repo = NewsRepository(db)
    news = repo.list_all()
    result = []
    for n in news:
        upvotes = repo.get_upvote_count(n.id)
        is_upvoted = repo.user_has_upvoted(n.id, current_user.id)
        result.append({**article_to_dict(n), "upvotes": upvotes, "is_upvoted": is_upvoted})
    return result

class PromptRequest(BaseModel):
    prompt: str

@app.post("/api/v1/news/search_news")
async def search_news(request: PromptRequest):
    prompt = request.prompt
    keyword_extraction_messages = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{prompt}"},
    ]

    keywords = openai_service.chat(keyword_extraction_messages)
    news_items = NewsService.fetch_news_info(keywords, is_initial=False)
    news_list = []
    for news_item in news_items:
        try:
            response = requests.get(news_item["titleLink"], timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            content_section = soup.find("section", class_="article-content__editor")

            paragraphs = [
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            detailed_news = {
                "url": news_item["titleLink"],
                "title": title,
                "time": time,
                "content": " ".join(paragraphs),
            }
            detailed_news["id"] = next(ARTICLE_ID_COUNTER)
            news_list.append(detailed_news)
        except Exception as exc:
            print(exc)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

class NewsSumaryRequestSchema(BaseModel):
    content: str

@app.post("/api/v1/news/news_summary")
async def news_summary(payload: NewsSumaryRequestSchema, u=Depends(authenticate_user_token)):
    response = {}
    summary_messages = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    result_text = openai_service.chat(summary_messages)
    if result_text:
        try:
            result = json.loads(result_text)
            response["summary"] = result.get("影響", "")
            response["reason"] = result.get("原因", "")
        except Exception:
            response["summary"] = ""
            response["reason"] = ""
    return response

@app.post("/api/v1/news/{id}/upvote")
def upvote_article(id: int, db: Session = Depends(get_db_session), current_user=Depends(authenticate_user_token)):
    repo = NewsRepository(db)
    message = repo.toggle_upvote(id, current_user.id)
    return {"message": message}

@app.get("/api/v1/prices/necessities-price")
def get_necessities_prices(category=Query(None), commodity=Query(None)):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
        timeout=10,
    ).json()
    