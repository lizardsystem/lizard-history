import logging
from lizard_ui import configchecker
from django.conf import settings

logger = logging.getLogger(__name__)


@configchecker.register
def checker():  # Pragma: nocover
    """Verify lizard_history's demands on settings.py."""
    if not ('lizard_history.middleware.HistoryMiddleware' in
        settings.MIDDLEWARE_CLASSES):
        logger.warn("you must add 'lizard_history.middleware.HistoryMiddleware' "
                    "to the list of MIDDLEWARE_CLASSES for the lizard_history "
                    "djangoapp to work.")
