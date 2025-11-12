# ensure models are imported so that Alembic and Base.metadata.create_all sees them
from app.models import news
from app.models import user

__all__ = ["news", "user"]