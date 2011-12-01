# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from mongoengine.signals import pre_save as mongo_pre_save
from mongoengine.signals import post_save as mongo_post_save
from mongoengine.signals import post_delete as mongo_post_delete

from django.db.models.signals import pre_save as django_pre_save
from django.db.models.signals import post_save as django_post_save
from django.db.models.signals import post_delete as django_post_delete

from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.contrib.admin.models import LogEntry

from lizard_history.handlers import pre_save_handler
from lizard_history.handlers import post_save_handler
from lizard_history.handlers import post_delete_handler

import lizard_history.configchecker
lizard_history.configchecker  # Pyflakes...

# Django models not to include in history tracking
EXCLUDED_MODELS = (
    Session,
)

# Mongoengin documents not to include in history tracking
EXCLUDED_DOCUMENTS = ()


@receiver(django_pre_save)
def django_pre_save_handler(sender, instance, raw, **kwargs):
    """
    Handle django_pre_save signal.
    """
    # Do nothing when loading fixtures, logging or when excluded
    if raw or sender == LogEntry or sender in EXCLUDED_MODELS:
        return

    pre_save_handler(sender, instance)


@receiver(django_post_save)
def django_post_save_handler(sender, instance, raw, **kwargs):
    """
    Handle django_post_save signal.
    """
    # Log nothing when loading fixtures, logging or when excluded
    if raw or sender == LogEntry or sender in EXCLUDED_MODELS:
        return

    post_save_handler(sender, instance)


@receiver(django_post_delete)
def django_post_delete_handler(sender, instance, **kwargs):
    """
    Handle django_post_delete signal.
    """
    if sender in EXCLUDED_MODELS:
        return

    post_delete_handler(sender, instance)


@receiver(mongo_pre_save)
def mongo_pre_save_handler(sender, document, **kwargs):
    """
    Handle django_pre_save signal.
    """
    if sender in EXCLUDED_DOCUMENTS:
        return

    pre_save_handler(sender, document)


@receiver(mongo_post_save)
def mongo_post_save_handler(sender, document, created):
    """
    Log a change or addition of a mongoengine document in the logentry.
    """
    if sender in EXCLUDED_DOCUMENTS:
        return

    post_save_handler(sender, document)


@receiver(mongo_post_delete)
def mongo_post_delete_handler(sender, document, *args, **kwargs):
    """
    Handle mongo_post_delete signal.
    """
    if sender in EXCLUDED_DOCUMENTS:
        return

    post_delete_handler(sender, document)
