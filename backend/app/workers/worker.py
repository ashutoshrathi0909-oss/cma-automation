"""ARQ worker configuration.

Run this worker with:
    arq app.workers.worker.WorkerSettings
"""

from arq.connections import RedisSettings

from app.config import get_settings
from app.workers.classification_tasks import run_classification
from app.workers.excel_tasks import run_excel_generation
from app.workers.extraction_tasks import run_extraction

settings = get_settings()


def _get_redis_settings(url: str | None = None) -> RedisSettings:
    """Parse a redis:// URL into an arq RedisSettings object.

    If *url* is not provided, reads from application config.

    Supports formats:
        redis://localhost:6379
        redis://redis:6379
        redis://redis:6379/0
    """
    if url is None:
        url = get_settings().redis_url

    # Strip scheme
    url = url.strip()
    if url.startswith("redis://"):
        url = url[len("redis://"):]

    # Remove database suffix (e.g. /0)
    if "/" in url:
        url = url.split("/")[0]

    # Split host:port
    if ":" in url:
        host, port_str = url.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            port = 6379
    else:
        host = url
        port = 6379

    return RedisSettings(host=host, port=port)


class WorkerSettings:
    """ARQ worker configuration class."""

    functions = [run_extraction, run_classification, run_excel_generation]
    redis_settings = _get_redis_settings()
    max_jobs = 10
    job_timeout = 300  # 5 minutes
