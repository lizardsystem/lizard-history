import logging
from lizard_ui import configchecker
from django.conf import settings

logger = logging.getLogger(__name__)


@configchecker.register
def checker():  # Pragma: nocover
    """Verify lizard_history's demands on settings.py."""
    if not ('tls.TLSRequestMiddleware' in
        settings.MIDDLEWARE_CLASSES):
        logger.warn("you must add 'tls.TLSRequestMiddleware' to the list of "
                    "MIDDLEWARE_CLASSES for the lizard_history djangoapp "
                    "to work.")
