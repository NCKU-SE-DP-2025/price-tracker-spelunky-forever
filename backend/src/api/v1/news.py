from fastapi import APIRouter, Depends, Query
from src.db.session import get_db_session
from src.repositories.news_repository import NewsRepository
from src.services.news_service import NewsService
from src.utils.openai_client import OpenAIService
from src.schemas.news import PromptRequest, NewsSummaryRequestSchema
from src.core.config import settings
from src.services.auth_service import AuthService
from fastapi.security import OAuth2PasswordBearer
import requests
from itertools import count
import json
import re
from typing import Any

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

# keep a counter like original ARTICLE_ID_COUNTER
ARTICLE_ID_COUNTER = count(start=1000000)

# helper to serialize articles (same as old article_to_dict)
def article_to_dict(article):
    return {
        "id": article.id,
        "url": article.url,
        "title": article.title,
        "time": article.time,
        "content": article.content,
        "summary": article.summary,
        "reason": article.reason,
    }

@router.get("/news")
def read_news(db=Depends(get_db_session)):
    repo = NewsRepository(db)
    news = repo.list_all()
    result = []
    for n in news:
        upvotes = repo.get_upvote_count(n.id)
        result.append({**article_to_dict(n), "upvotes": upvotes, "is_upvoted": False})
    return result

@router.get("/user_news")
def read_user_news(token: str = Depends(oauth2_scheme), db=Depends(get_db_session)):
    auth_service = AuthService(db, secret_key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    current_user = auth_service.authenticate_token(token)

    repo = NewsRepository(db)
    news = repo.list_all()
    result = []
    for tmp_news in news:
        upvotes = repo.get_upvote_count(tmp_news.id)
        is_upvoted = repo.user_has_upvoted(tmp_news.id, current_user.id)
        result.append({**article_to_dict(tmp_news), "upvotes": upvotes, "is_upvoted": is_upvoted})
    return result

@router.post("/search_news")
def search_news(request: PromptRequest,db=Depends(get_db_session)):
    prompt = request.prompt
    openai_client = OpenAIService(settings.OPENAI_API_KEY)
    news_service = NewsService(db, openai_client)
    keyword_extraction_messages = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{prompt}"},
    ]

    keywords = openai_client.chat(keyword_extraction_messages)
    news_list = news_service.search_and_parse(keywords)
    for news in news_list:
        news["id"] = next(ARTICLE_ID_COUNTER)

    return news_list

@router.post("/news_summary")
def news_summary(payload: NewsSummaryRequestSchema, token: str = Depends(oauth2_scheme), db=Depends(get_db_session)):
    # require auth same as before
    auth_service = AuthService(db, secret_key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    _ = auth_service.authenticate_token(token)

    response = {}
    openai_client = OpenAIService(settings.OPENAI_API_KEY)
    summary_messages = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{payload.content}"},
    ]

    result_text = openai_client.chat(summary_messages)
    def _try_json_loads_once(s: str):
        try:
            return json.loads(s)
        except Exception:
            return None

    # 若是 bytes -> 轉 str
    if isinstance(result_text, (bytes, bytearray)):
        try:
            result_text = result_text.decode("utf-8")
        except Exception:
            result_text = result_text.decode("utf-8", errors="ignore")

    parsed: Any = None

    # 如果已經是 dict/list，就直接使用
    if isinstance(result_text, (dict, list)):
        parsed = result_text
    elif isinstance(result_text, str):
        # 連續嘗試 json.loads（處理 double-encoded），上限 3 次
        attempt = 0
        cur = result_text
        while attempt < 3:
            loaded = _try_json_loads_once(cur)
            if loaded is None:
                break
            # 若載入後仍是字串，代表還包了一層 json 字串 -> 繼續嘗試
            if isinstance(loaded, str):
                cur = loaded
                attempt += 1
                continue
            # 成功解析為 dict/list/其他物件
            parsed = loaded
            break
        # 如果第一次 json.loads 直接得到 None（不能解析），則不處理 parsed（保持 None）
    else:
        parsed = None

    # 遞迴把字串中 literal 的 unicode escape (\uXXXX 或 \\uXXXX) 轉成真實 unicode
    _unicode_escape_pattern = re.compile(r"(?:\\\\u|\\u)[0-9a-fA-F]{4}")

    def _decode_str_if_needed(s: str) -> str:
        # 只有在字串含有 \u 或 \\u 才嘗試解碼，避免誤改其它字串
        if not isinstance(s, str):
            return s
        if _unicode_escape_pattern.search(s):
            try:
                # 使用 unicode_escape 將 \uXXXX 轉回對應 character
                return s.encode("utf-8").decode("unicode_escape")
            except Exception:
                # 若失敗則返回原字串
                return s
        return s

    def _recursively_decode(obj: Any) -> Any:
        if isinstance(obj, dict):
            new = {}
            for k, v in obj.items():
                new_k = _decode_str_if_needed(k) if isinstance(k, str) else k
                new_v = _recursively_decode(v)
                new[new_k] = new_v
            return new
        if isinstance(obj, list):
            return [_recursively_decode(i) for i in obj]
        if isinstance(obj, str):
            return _decode_str_if_needed(obj)
        return obj

    if parsed is not None:
        parsed = _recursively_decode(parsed)

    # 取值（優先以中文 key，若沒則嘗試 unicode escape key 的 fallback）
    if isinstance(parsed, dict):
        summary_val = parsed.get("影響", "")
        reason_val = parsed.get("原因", "")
        response["summary"] = summary_val or ""
        response["reason"] = reason_val or ""
    else:
        response["summary"] = ""
        response["reason"] = ""

    return response

@router.post("/{id}/upvote")
def upvote_article(id: int, token: str = Depends(oauth2_scheme), db=Depends(get_db_session)):
    auth_service = AuthService(db, secret_key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    current_user = auth_service.authenticate_token(token)
    repo = NewsRepository(db)
    message = repo.toggle_upvote(id, current_user.id)
    return {"message": message}

@router.get("/prices/necessities-price")
def get_necessities_prices(category: str = Query(None), commodity: str = Query(None)):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
        timeout=10,
    ).json()
