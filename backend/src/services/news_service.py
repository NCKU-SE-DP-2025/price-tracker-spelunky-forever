import json
from src.utils.scraper import Scraper
from src.repositories.news_repository import NewsRepository
from src.crawler.udn_crawler import UDNCrawler
from src.crawler.crawler_base import News

class NewsService:
    def __init__(self, db, openai_client):
        self.db = db
        self.openai = openai_client
        self.repo = NewsRepository(db)
        self.crawler = UDNCrawler(timeout=10)

    @staticmethod
    def fetch_news_info(self, search_term):
        return self.crawler.get_headline(search_term, page=(1,10))

    def search_and_parse(self, keyword: str):
        headlines = self.fetch_news_info(keyword)
        news_list = []
        for tmp_headlines in headlines:
            try:
                news_obj = self.crawler.parse(tmp_headlines.url)
                detailed_news = {
                    "id": 0, # 暫時 ID，因為還沒存入 DB
                    "url": news_obj.url,
                    "title": news_obj.title,
                    "time": news_obj.time,
                    "content": news_obj.content,
                }
                news_list.append(detailed_news)
            except Exception as e:
                print(f"Error parsing {tmp_headlines.url}: {e}")
                continue

        return sorted(news_list, key=lambda x: x["time"], reverse=True)

    def assess_and_store(self):
        headlines = self.fetch_news_info("價格")
        for tmp_headlines in headlines:
            article_title = tmp_headlines.title
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
                    news_obj = self.crawler.parse(tmp_headlines.url)
                    summary_messages = [
                        {
                            "role": "system",
                            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                        },
                        {"role": "user", "content": news_obj.content},
                    ]
                    result_text = self.openai.chat(summary_messages)

                    summary_data = {"影響": "", "原因": ""}
                    try:
                        summary_data = json.loads(result_text)
                    except Exception:
                        pass

                    self.crawler.save(news_obj, self.db)
                except Exception as exc:
                    print("error fetching/storing article:", exc)
