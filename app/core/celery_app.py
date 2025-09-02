from celery import Celery
from app.core.config import settings
from kombu import Queue, Exchange

celery_app = Celery(
    "scraper_dashboard",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Add this line to auto-discover tasks
celery_app.autodiscover_tasks(["app.worker"])

celery_app.config_from_object(settings, namespace="CELERY")

# Optional configurations
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_hijack_root_logger=False,
    worker_redirect_stdouts=False,
)


celery_app.conf.task_default_exchange = "main"
celery_app.conf.task_default_routing_key = "main"
celery_app.conf.task_queues = (
    Queue(
        "main",
        exchange=Exchange("main", type="direct"),
        routing_key="main",
        queue_arguments={
            "x-max-priority": 10,
            "x-message-ttl": 86400000,  # 24 hours TTL
        },
    ),
    # Queue(
    #     "control",
    #     exchange=Exchange("control", type="direct"),
    #     routing_key="control",
    #     queue_arguments={
    #         "x-max-priority": 255,
    #         "x-message-ttl": 3600000,
    #     },
    # ),
)

# celery_app.conf.task_routes = {
#     "app.worker.tasks_scripts.run_script": {"queue": "main"},
#     "app.worker.tasks_scripts.stop_script": {"queue": "control"},
# }
