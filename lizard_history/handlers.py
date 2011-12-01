# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.utils.encoding import force_unicode

from django.contrib.admin.models import LogEntry
from django.contrib.admin.models import ADDITION
from django.contrib.admin.models import CHANGE
from django.contrib.admin.models import DELETION

from lizard_history.utils import object_hash
from lizard_history.utils import format_diff
from lizard_history.utils import user_pk
from lizard_history import utils

from tls import request


def pre_save_handler(sender, obj):
    """
    Store the original object on the request if it exists.
    """

    obj._lizard_history_hash = object_hash(obj)
    if not hasattr(request, 'lizard_history'):
        request.lizard_history = {}

    if obj.pk is None:
        original = None
    else:
        try:
            original = sender.objects.get(pk=obj.pk)
        except sender.DoesNotExist:
            original = None

    # Store the original object on the request
    request.lizard_history.update({
        obj._lizard_history_hash: original,
    })


def post_save_handler(sender, obj):
    """
    Log a change or addition of an object in the logentry.
    """

    # Retrieve the original object from the request, if any
    original = request.lizard_history.get(obj._lizard_history_hash)

    if original:
        action_flag = CHANGE
    else:
        action_flag = ADDITION

    diff = utils.diff(
        utils.to_json(original),
        utils.to_json(obj),
    )

    # Don't log if nothing was changed.
    if not diff:
        return

    change_message = format_diff(diff)

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=utils.user_pk(),
        content_type_id=utils.get_contenttype_id(obj),
        object_id=obj.pk,
        object_repr=force_unicode(obj),
        action_flag=action_flag,
        change_message=change_message,
    )


def post_delete_handler(sender, obj):
    """
    Log the deletion of an object in the logentry.
    """

    # Set action_flag and change message
    action_flag = DELETION
    diff = utils.diff(
        utils.to_json(obj),
        utils.to_json(None),
    )
    change_message = format_diff(diff)

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=user_pk(),
        content_type_id=utils.get_contenttype_id(obj),
        object_id=obj.pk,
        object_repr=force_unicode(obj),
        action_flag=action_flag,
        change_message=change_message,
    )
