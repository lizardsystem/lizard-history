# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from mongoengine.signals import pre_save as mongo_pre_save
from mongoengine.signals import post_save as mongo_post_save
from mongoengine.signals import post_delete as mongo_post_delete

from django.db.models.signals import pre_save as django_pre_save
from django.db.models.signals import post_save as django_post_save
from django.db.models.signals import post_delete as django_post_delete

from django.db import models
from django.db.utils import DatabaseError

from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.contrib.admin.models import LogEntry
from django.utils.translation import ugettext_lazy as _
# from django.utils.db import DatabaseError

from lizard_history.handlers import pre_save_handler
from lizard_history.handlers import post_save_handler
from lizard_history.handlers import post_delete_handler

import lizard_history.configchecker
lizard_history.configchecker  # Pyflakes...


def _is_monitored(sender):
    """
    Return if the sender is to be monitored.

    LogEntry is hardcoded here because monitoring logentry creates a loop
    ContentType is excluded to be able to syncdb
    """

    if sender == LogEntry:
        # Prevent a loop
        return
    
    try:
        return MonitoredModel.objects.filter(
            app_label=sender.__module__.split('.')[0],
            model=sender.__name__.lower()).exists()
    except DatabaseError:
        return False



@receiver(django_pre_save)
def django_pre_save_handler(sender, instance, raw, **kwargs):
    """
    Handle django_pre_save signal.
    """
    # Do nothing when loading fixtures, logging or not monitored
    if raw or not _is_monitored(sender):
        return

    pre_save_handler(sender, instance)


@receiver(django_post_save)
def django_post_save_handler(sender, instance, raw, **kwargs):
    """
    Handle django_post_save signal.
    """
    # Do nothing when loading fixtures, logging or not monitored
    if raw or not _is_monitored(sender):
        return

    post_save_handler(sender, instance)


@receiver(django_post_delete)
def django_post_delete_handler(sender, instance, **kwargs):
    """
    Handle django_post_delete signal.
    """
    if not _is_monitored(sender):
        return

    post_delete_handler(sender, instance)


@receiver(mongo_pre_save)
def mongo_pre_save_handler(sender, document, **kwargs):
    """
    Handle django_pre_save signal.
    """
    if not _is_monitored(sender):
        return

    pre_save_handler(sender, document)


@receiver(mongo_post_save)
def mongo_post_save_handler(sender, document, created):
    """
    Log a change or addition of a mongoengine document in the logentry.
    """
    if not _is_monitored(sender):
        return

    post_save_handler(sender, document)


@receiver(mongo_post_delete)
def mongo_post_delete_handler(sender, document, *args, **kwargs):
    """
    Handle mongo_post_delete signal.
    """
    if not _is_monitored(sender):
        return

    post_delete_handler(sender, document)


class MonitoredModel(models.Model):
    name = models.CharField(max_length=100)
    app_label = models.CharField(max_length=100)
    model = models.CharField(_('python model class name'), max_length=100)

    class Meta:
        verbose_name = _('monitored model')
        verbose_name_plural = _('monitored models')
        ordering = ('app_label', 'model',)
        unique_together = (('app_label', 'model'),)

    def __unicode__(self):
        return self.name

