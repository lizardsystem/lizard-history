# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.db import models
from django.dispatch import receiver

from django.utils.translation import ugettext_lazy as _

from lizard_history import (
    handlers,
    signals,
)

import lizard_history.configchecker
lizard_history.configchecker  # Pyflakes...

# Need these models to check for excluded models
from south.models import MigrationHistory
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.contrib.admin.models import LogEntry
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

# Some models are excluded here since they are involved in the process
# of setting up the site
EXCLUDED_MODELS = [
    MigrationHistory,
    ContentType,
    Permission,
    LogEntry,  # Prevent a loop
    Site,
    User,
]

signals.ops_done.connect(handlers.process_request_handler)


def _is_monitored(sender):
    """
    Return if the sender is to be monitored.
    """
    if sender in EXCLUDED_MODELS:
        return False

    return MonitoredModel.objects.filter(
        app_label=sender.__module__.split('.')[0],
        model=sender.__name__.lower(),
    ).exists()


@receiver(models.signals.pre_save)
def pre_save_handler(sender, instance, **kwargs):
    if _is_monitored(sender):
        kwargs.update(signal_name='pre_save')
        handlers.db_handler(sender, instance, **kwargs)


@receiver(models.signals.post_save)
def post_save_handler(sender, instance, **kwargs):
    #print '************ Saving: *****************'
    #print instance

    if _is_monitored(sender):
        kwargs.update(signal_name='post_save')
        handlers.db_handler(sender, instance, **kwargs)


@receiver(models.signals.pre_delete)
def pre_delete_handler(sender, instance, **kwargs):
    if _is_monitored(sender):
        kwargs.update(signal_name='pre_delete')
        handlers.db_handler(sender, instance, **kwargs)


@receiver(models.signals.post_delete)
def post_delete_handler(sender, instance, **kwargs):
    if _is_monitored(sender):
        kwargs.update(signal_name='post_delete')
        handlers.db_handler(sender, instance, **kwargs)


@receiver(models.signals.m2m_changed)
def m2m_changed_handler(sender, instance, **kwargs):
    if _is_monitored(sender):
        kwargs.update(signal_name='m2m_changed')
        handlers.db_handler(sender, instance, **kwargs)


class MonitoredModel(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )
    app_label = models.CharField(
        max_length=100,
        verbose_name=_('App label'),
    )
    model = models.CharField(
        max_length=100,
        verbose_name=_('Django model name'),
    )

    class Meta:
        verbose_name = _('Monitored model')
        verbose_name_plural = _('Monitored models')
        ordering = ('app_label', 'model',)
        unique_together = (('app_label', 'model'),)

    def __unicode__(self):
        return self.name
