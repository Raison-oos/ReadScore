import os
import sys
import socket
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


def has_internet(host="huggingface.co", port=443, timeout=2.0) -> bool:
    """
    Plain TCP connectivity check — has nothing to do with Hugging Face's
    own offline-mode machinery, so it's safe to call before anything
    from transformers/huggingface_hub is ever imported.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False


# Management commands that never touch the ML models — no reason to pay
# the model-loading cost for these.
NON_SERVING_COMMANDS = {
    "makemigrations", "migrate", "check", "shell", "test",
    "collectstatic", "createsuperuser", "dbshell", "showmigrations",
}


class ClassroomConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "classroom"

    def ready(self):
        command = sys.argv[1] if len(sys.argv) > 1 else None

        if command in NON_SERVING_COMMANDS:
            return
        if command == "runserver" and os.environ.get("RUN_MAIN") != "true":
            return

        # Decide ONCE, before transformers/huggingface_hub is imported
        # anywhere in this process. Their internal offline/online state
        # is fixed at first import and cannot be changed afterward by
        # toggling the env vars later.
        if has_internet():
            os.environ.pop("HF_HUB_OFFLINE", None)
            os.environ.pop("TRANSFORMERS_OFFLINE", None)
            logger.info("Internet detected — models will load online if not cached.")
        else:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            logger.info("No internet detected — forcing offline mode (local cache only).")

        from .ml.classifier import get_classifier
        from .ml.answer_scorer import get_scorer

        try:
            get_classifier()
            get_scorer()
            logger.info("ML models loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            raise