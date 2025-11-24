"""
UDN News Scraper Module

This module provides the UDNCrawler class for fetching, parsing, and saving news articles from the UDN website.
The class extends the NewsCrawlerBase and includes functionalities to search for news articles based on a search term,
parse the details of individual articles, and save them to a database using SQLAlchemy ORM.

Classes:
    UDNCrawler: A class to scrape news from UDN.

Exceptions:
    DomainMismatchException: Raised when the URL domain does not match the expected domain for the crawler.

Usage Example:
    crawler = UDNCrawler(timeout=10)
    headlines = crawler.startup("technology")
    for headline in headlines:
        news = crawler.parse(headline.url)
        crawler.save(news, db_session)

UDNCrawler Methods:
    __init__(self, timeout: int = 5): Initializes the crawler with a default timeout for HTTP requests.
    startup(self, search_term: str) -> list[Headline]: Fetches news headlines for a given search term across multiple pages.
    get_headline(self, search_term: str, page: int | tuple[int, int]) -> list[Headline]: Fetches news headlines for specified pages.
    _fetch_news(self, page: int, search_term: str) -> list[Headline]: Helper method to fetch news headlines for a specific page.
    _create_search_params(self, page: int, search_term: str): Creates the parameters for the search request.
    _perform_request(self, params: dict): Performs the HTTP request to fetch news data.
    _parse_headlines(response): Parses the response to extract headlines.
    parse(self, url: str) -> News: Parses a news article from a given URL.
    _extract_news(soup, url: str) -> News: Extracts news details from the BeautifulSoup object.
    save(self, news: News, db: Session): Saves a news article to the database.
    _commit_changes(db: Session): Commits the changes to the database with error handling.
"""

from requests import Response
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
import requests
from urllib.parse import quote
from src.models.news import NewsArticle
from src.services.news_service import NewsService

from crawler_base import NewsCrawlerBase, Headline, News, NewsWithSummary


class UDNCrawler(NewsCrawlerBase):
    CHANNEL_ID = 2

    def __init__(self, timeout: int = 5) -> None:
        self.news_website_url = "https://udn.com/api/more"
        self.timeout = timeout

    def startup(self, search_term: str) -> list[Headline]:
        """
        Initializes the application by fetching news headlines for a given search term across multiple pages.
        This method is typically called at the beginning of the program when there is no data available,
        hence it fetches headlines from the first 10 pages.

        :param search_term: The term to search for in news headlines.
        :return: A list of Headline namedtuples containing the title and URL of news articles.
        :rtype: list[Headline]
        """
        return self.get_headline(search_term, page=(1, 10))

    def get_headline(self, search_term: str, page: int | tuple[int, int]) -> list[Headline]:
        # Calculate the range of pages to fetch news from.
        # If 'page' is a tuple, unpack it and create a range representing those pages (inclusive).
        # If 'page' is an int, create a list containing only that single page number.
        # page_range = range(*page) if isinstance(page, tuple) else [page]
        all_headlines=[]
        if isinstance(page,tuple):
            start_page,end_page=page
            page_list=range(start_page,end_page+1)
        else:
            page_list=[page]
        
        for temp_page in page_list:
            all_headlines.extend(self._fetch_news(temp_page,search_term))

        return all_headlines

    def _fetch_news(self, search_page: int, search_term: str) -> list[Headline]:
        news_data = []
        page_params = self._create_search_params(search_page,search_term)
        response = self._perform_request("https://udn.com/api/more",page_params)
        news_data = response.json().get("lists", [])
        return news_data

    def _create_search_params(self, search_page: int, search_term: str) -> dict:
        return {
                "page": search_page,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
        }

    def _perform_request(self, url: str | None = None, params: dict | None = None) -> Response:
        return requests.get(url, params=params, timeout=10)

    @staticmethod
    def _parse_headlines(response: Response) -> list[Headline]:
        data = response.json()
        return response.json().get("lists", [])

    def parse(self, url: str) -> News:
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        soup=BeautifulSoup(response.text,'html.parser')
        return self._extract_news(soup,url)

    @staticmethod
    def _extract_news(soup: BeautifulSoup, url: str) -> News:
        title=soup.select_one('h1.article-content__title').text.strip()
        time=soup.select_one('time.article-content__time').text.strip()
        raw_content=soup.select_one('section.article-content__editor')
        content_list=[]
        paragrapghs=raw_content.select('p')
        for tmp_paragraphas in paragrapghs:
            if(tmp_paragraphas.text.strip()):
                content_list.append(tmp_paragraphas.text.strip())
        content= "\n".join(content_list)

        return News(
            title=title,
            url=url,
            time=time,
            content=content
        )

    def save(self, news: News, db: Session):
        if db.query(NewsArticle).fliter(NewsArticle.url==str(news.url)).first():
            return None
        in_data=NewsArticle(
            url = news.url,
            title = news.title,
            time = news.time,
            content = news.content,
            summary = None,
            reason = None
        )
        db.add(in_data)
        self._commit_changes(db)

    @staticmethod
    def _commit_changes(db: Session):
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"DB commit failed. Already Rollback. error: {e}")

# if __name__ == "__main__":
#     # 建立爬蟲實例
#     crawler = UDNCrawler()
    
#     # 測試抓取 "台積電" 的新聞
#     print("開始測試爬取...")
#     headlines = crawler.get_headline(search_term="台積電", page=1)
    
#     print(f"\n總共抓到 {len(headlines)} 則標題：")
#     for h in headlines:
#         print(h)