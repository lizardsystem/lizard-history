# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from django.contrib.admin.models import LogEntry
from lizard_history import utils
from tls import request


def db_handler(sender, instance, **kwargs):
    """
    Store old and new objects on the request.
    """
    if not request or kwargs.get('raw', False):
        return

    if kwargs.get('name').startswith('pre'):

        # Give object a unique id.
        instance._lizard_history_hash = utils.object_hash(instance)
        
        
        # Try to retrieve old version from database.
        if instance.pk is None:
            old = None
        else:
            try:
                old = sender.objects.get(pk=instance.pk)
            except sender.DoesNotExist:
                old = None

        # Store the original object on the request
        if not hasattr(request, 'lizard_history'):
            request.lizard_history = {}
        request.lizard_history.update({
            instance._lizard_history_hash: {
                'old': old,
                'phase': kwargs.get('name'),
            }
        })

    if kwargs.get('name').startswith('post_'):
        request.lizard_history[instance._lizard_history_hash].update({
            'new': instance if kwargs.get('name') == 'post_save' else None,
            'phase': kwargs.get('name'),
        })

def request_handler(**kwargs):
    """
    Log any changes recorded on the request object.
    """
    if not hasattr(request, 'lizard_history'):
        return

        
    from pprint import pprint
    pprint(request.lizard_history)
    for action in request.lizard_history.items():
        pass


def request_ended_handler(sender):
    """
    Save all changes in the context of this request into the logentry
    """
    # Retrieve the original object from the request, if any
    original = request.lizard_history.get(obj._lizard_history_hash)

    if original:
        action_flag = LIZARD_CHANGE
    else:
        action_flag = LIZARD_ADDITION

    change_message = utils.change_message(
        obj1=original,
        obj2=obj,
        summary=getattr(obj, 'lizard_history_summary', ''),
    )

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
    """ Deletion """

    # Set action_flag and change message
    action_flag = LIZARD_DELETION
    change_message = utils.change_message(
        obj1=obj,
        obj2=None,
        summary=getattr(obj, 'lizard_history_summary', ''),
    )

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=user_pk(),
        content_type_id=utils.get_contenttype_id(obj),
        object_id=obj.pk,
        object_repr=force_unicode(obj),
        action_flag=action_flag,
        change_message=change_message,
    )
