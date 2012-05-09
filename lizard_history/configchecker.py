import logging
from lizard_ui import configchecker
from django.conf import settings

logger = logging.getLogger(__name__)


@configchecker.register
def checker():  # Pragma: nocover
    """Verify lizard_history's demands on settings.py."""

    if (
        'tls.TLSRequestMiddleware' in
        settings.MIDDLEWARE_CLASSES and
        'lizard_history.middleware.HistoryMiddleware' in
        settings.MIDDLEWARE_CLASSES
    ):
        if (
            settings.MIDDLEWARE_CLASSES.index(
                'tls.TLSRequestMiddleware',
            ) >
            settings.MIDDLEWARE_CLASSES.index(
                'lizard_history.middleware.HistoryMiddleware',
            )
        ):
            logger.warn(
                "'tls.TLSRequestMiddleware' must come before "
                "'lizard_history.middleware.HistoryMiddleware' in the list of "
                "MIDDLEWARE_CLASSES for the lizard_history djangoapp to work. "
            )
    else:
        if not ('tls.TLSRequestMiddleware' in
            settings.MIDDLEWARE_CLASSES):
            logger.warn(
                "you must add 'tls.TLSRequestMiddleware' "
                "to the list of MIDDLEWARE_CLASSES for the lizard_history "
                "djangoapp to work.")
        if not ('lizard_history.middleware.HistoryMiddleware' in
            settings.MIDDLEWARE_CLASSES):
            logger.warn(
                "you must add 'lizard_history.middleware.HistoryMiddleware' "
                "to the list of MIDDLEWARE_CLASSES for the lizard_history "
                "djangoapp to work."
            )
