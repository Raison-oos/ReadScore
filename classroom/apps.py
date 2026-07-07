import sys
from django.apps import AppConfig


class ClassroomConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "classroom"

    def ready(self):
        import os

        # Under `runserver`, the autoreloader spawns this ready() twice —
        # once in a parent watcher process, once in the real worker. Skip
        # the parent so models only load once. This check is a no-op
        # (RUN_MAIN unset) under gunicorn/uwsgi in production, so
        # production loading is unaffected.
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return

        from .ml.classifier import get_classifier
        from .ml.answer_scorer import get_scorer

        get_classifier()
        get_scorer()