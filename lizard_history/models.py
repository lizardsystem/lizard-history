# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from mongoengine.signals import pre_save as mongo_pre_save
from mongoengine.signals import post_save as mongo_post_save
from mongoengine.signals import post_delete as mongo_post_delete

from django.db.models.signals import pre_save as django_pre_save
from django.db.models.signals import post_save as django_post_save
from django.db.models.signals import post_delete as django_post_delete
from django.db.models.signals import m2m_changed as django_m2m_changed

from django.db import models
from django.db.utils import DatabaseError

from django.dispatch import receiver
from django.contrib.sessions.models import Session

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from south.models import MigrationHistory

from django.utils.translation import ugettext_lazy as _
# from django.utils.db import DatabaseError

from lizard_history.handlers import pre_save_handler
from lizard_history.handlers import post_save_handler
from lizard_history.handlers import post_delete_handler

import lizard_history.configchecker
lizard_history.configchecker  # Pyflakes...

# Some models are excluded here since they are involved in the process
# of setting up the site
EXCLUDED_MODELS = [
    LogEntry,  # Prevent a loop
    ContentType,
    Permission,
    Site,
    MigrationHistory,
    User
]

def _is_monitored(sender):
    """
    Return if the sender is to be monitored.
    """
    if sender in EXCLUDED_MODELS:
        return False
    
    return MonitoredModel.objects.filter(
        app_label=sender.__module__.split('.')[0],
        model=sender.__name__.lower()).exists()


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


@receiver(django_m2m_changed)
def django_m2m_changed_handler(sender, instance, action,
                               reverse, model, pk_set, **kwargs):
    """
    Handle change_m2m signal.
    """
    pass
#   print sender
#   print instance
#   print action
#   print reverse
#   print model
#   print pk_set
#   print kwargs
#   if not _is_monitored(instance):
#       return

#   change_m2m_handler(sender, instance)


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

