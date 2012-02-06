# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.utils.encoding import force_unicode

from django.contrib.admin.models import LogEntry

from lizard_history.utils import LIZARD_ADDITION
from lizard_history.utils import LIZARD_CHANGE
from lizard_history.utils import LIZARD_DELETION
from lizard_history.utils import object_hash
from lizard_history.utils import user_pk
from lizard_history import utils

from tls import request


# We take other values than Django to distuingish from
# Django's own entries.

def pre_save_handler(sender, obj):
    """
    Store the original object on the request if it exists.
    """
    if not request:
        return

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
    if not request:
        return

    # If models with m2m fields are handled by the m2m_changed_handler
#   if obj._meta.many_to_many:
#       return

    # Retrieve the original object from the request, if any
    original = request.lizard_history.get(obj._lizard_history_hash)

    if original:
        action_flag = LIZARD_CHANGE
    else:
        action_flag = LIZARD_ADDITION

    change_message = utils.diff(original, obj)

    # Don't log if nothing was changed.
    if not change_message:
        return

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
    if not request:
        return

    # Set action_flag and change message
    action_flag = LIZARD_DELETION
    change_message = utils.diff(obj, None)

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=user_pk(),
        content_type_id=utils.get_contenttype_id(obj),
        object_id=obj.pk,
        object_repr=force_unicode(obj),
        action_flag=action_flag,
        change_message=change_message,
    )

def m2m_changed_handler(sender, instance, action,
                        reverse, model, pk_set, **kwargs):
    """
    Log the change of a m2m relation of an object in the logentry.
    """
    if not request:
        return
    print '------------------------------'
#   print sender
#   print instance
    print action
    print reverse
#   print model
    print pk_set
    from lizard_history.utils import _model_dict
    print _model_dict(instance)
    print kwargs
    print '------------------------------'
