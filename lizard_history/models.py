# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.db.models.signals import pre_save
#from django.db.models.signals import post_save
#from django.db.models.signals import pre_delete
from django.db.models.signals import post_delete
from django.db.models import Model

from django.dispatch import receiver

from django.utils.encoding import force_unicode
from django.utils import simplejson

from django.core.serializers import serialize

from django.contrib.contenttypes.models import ContentType

from django.contrib.sessions.models import Session

from django.contrib.admin.models import LogEntry
from django.contrib.admin.models import ADDITION
from django.contrib.admin.models import CHANGE
from django.contrib.admin.models import DELETION

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser


from tls import request

import logging
import pprint

import lizard_history.configchecker
lizard_history.configchecker  # Pyflakes...

logger = logging.getLogger()

EXCLUDED_MODELS = (
    Session,
)


def _dict_diff(dict1, dict2):
    """
    Return a dict with the changes going from obj1 to obj2.
    """
    return dict(set(dict2.iteritems()) -
                set(dict1.iteritems()))


def _model_dict(instance):
    """
    Return a dict representing the django model.

    We use the django serializer here.
    """
    return serialize('python', [instance])[0]['fields']


def _user_pk():
    """ Determine the user for this request."""
    if not request or isinstance(request.user, AnonymousUser):
        # Get the first superuser
        return User.objects.filter(is_superuser=True)[0].pk
    return request.user.pk


@receiver(pre_save)
def pre_save_handler(sender, instance, raw, **kwargs):
    """
    Put a save or change entry in the logentry.
    """
    if raw:
        # A fixture is loaded, may be we don't want to log
        # any fixtures loaded?
        return

    if sender == LogEntry:
        # We must prevent LogEntries to trigger new LogEntries to be saved.
        logger.debug('logging into LogEntry:\n%s',
                     pprint.pformat(instance.__dict__))
        return

    if sender in EXCLUDED_MODELS:
        return

    # Determine the type of action, and an appropriate change message
    try:
        original = sender.objects.get(pk=instance.pk)
        action_flag = CHANGE
        change_message = simplejson.dumps(_dict_diff(
            _model_dict(original),
            _model_dict(instance),
        ))
    except sender.DoesNotExist:
        action_flag = ADDITION
        change_message = simplejson.dumps(_model_dict(instance))

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=_user_pk(),
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=force_unicode(instance),
        action_flag=action_flag,
        change_message=change_message,
    )


@receiver(post_delete)
def post_delete_handler(sender, instance, **kwargs):
    """
    Put a delete entry in the logentry.
    """
    if sender in EXCLUDED_MODELS:
        return

    # Set action_flag and change message
    action_flag = DELETION
    change_message = simplejson.dumps(_model_dict(instance))

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=_user_pk(),
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=force_unicode(instance),
        action_flag=action_flag,
        change_message=change_message,
    )
