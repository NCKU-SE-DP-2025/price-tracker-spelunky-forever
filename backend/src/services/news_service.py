import json
from urllib.parse import quote
import requests
from src.utils.scraper import Scraper
from src.repositories.news_repository import NewsRepository

class NewsService:
    def __init__(self, db, openai_client):
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
