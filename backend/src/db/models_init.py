# ensure models are imported so that Alembic and Base.metadata.create_all sees them
from src.models import news
from src.models import user

__all__ = ["news", "user"]