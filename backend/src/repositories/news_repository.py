from sqlalchemy import delete, insert
from src.models.news import NewsArticle, user_news_association_table

class NewsRepository:
    def __init__(self, db):
        self.db = db

    def save_article(self, news_data: dict):
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