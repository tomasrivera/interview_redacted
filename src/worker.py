import time
from logging import getLogger

from celery import Celery

from src.settings import settings

celery = Celery(
    __name__,
    broker=settings.celery_broker,
    backend=settings.celery_result_backend,
)

logger = getLogger(__name__)


@celery.task(name="create_task")
def create_task(task_type: float) -> bool:
    logger.info("STARTED")
    time.sleep(int(task_type))
    logger.info("FINISHED")
    return True
