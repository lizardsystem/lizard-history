# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

#from django.db.models.signals import pre_save
from django.db.models.signals import post_save
# from django.db.models.signals import pre_delete
from django.db.models.signals import post_delete

from django.dispatch import receiver

from django.utils.encoding import force_unicode
from django.utils import simplejson

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


MSG_NO_USER = """
%s.%s inherits from lizard_history,
but no user or request is set on the object when saving. Lizard_history
cannot determine the user responsible for this save action; defaulting
to first superuser found."""

EXCLUDED_MODELS = (
    Session,
)


def _dict_diff(dict1, dict2):
    """
    Return a dict with the changes going from obj1 to obj2.
    """
    return dict(set(dict2.iteritems()) -
                set(dict1.iteritems()))


def _instance_dict(instance):
    """
    Return the instance dict without the state object.
    """
    result = instance.__dict__.copy()
    del result['_state']
    return result


# Get the first superuser, who will be framed into an admin role...
admin = User.objects.filter(is_superuser=True)[0]
logger = logging.getLogger(__name__)


@receiver(post_save)
def post_save_handler(sender, instance, created, raw, **kwargs):
    """
    Add an entry in the logentry
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

    # Determine the user
    if not request or isinstance(request.user, AnonymousUser):
        logger.warn(MSG_NO_USER % (
            instance.__module__,
            instance.__class__.__name__,
        ))
        # Get the first superuser
        user_pk = User.objects.filter(is_superuser=True)[0].pk
    else:
        user_pk = request.user.pk

    # Determine the type of action. Unfortunately,
    # we have to query the object to see if it will be an update or
    # an insert.
    try:
        original = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        original = sender()

    if original.pk:
        action_flag = CHANGE
    else:
        action_flag = ADDITION

    change_message = simplejson.dumps(_dict_diff(
        _instance_dict(original),
        _instance_dict(instance),
    ))

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=user_pk,
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=force_unicode(instance),
        action_flag=action_flag,
        change_message=change_message,
    )


@receiver(post_save)
def post_save_handler(sender, instance, created, raw, **kwargs):
    pass
