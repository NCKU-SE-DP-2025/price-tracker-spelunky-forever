import sentry_sdk
from .config import settings

# initialize sentry as old main did
def init_sentry(settings):
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )