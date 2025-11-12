import requests
from bs4 import BeautifulSoup

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