# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.utils.encoding import force_unicode

from django.contrib.admin.models import LogEntry
from lizard_history import utils
from lizard_esf.models import AreaConfiguration
from tls import request

import lizard_wbconfiguration  # Beware of conflicting AreaConfiguration
                               # in lizard_esf.models

WBCONFIGURATION_CLASSES = (
    lizard_wbconfiguration.models.AreaConfiguration,
    lizard_wbconfiguration.models.Structure,
    lizard_wbconfiguration.models.Bucket,
)


def db_handler(sender, instance, **kwargs):
    """
    Store old and new objects on the request.
    """
    if not request or kwargs.get('raw', False):
        return

    # Try to retrieve database version of instance.
    try:
        db_copy = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        db_copy = None

    if kwargs.get('signal_name').startswith('pre'):

        # Give object a unique id for identification in subsequent signals
        instance._lizard_history_hash = utils.object_hash(instance)

        # Store the original object on the request
        if not hasattr(request, 'lizard_history'):
            request.lizard_history = {}

        request.lizard_history.update({
            instance._lizard_history_hash: {
                'pre_copy': db_copy,
                'signal_name': kwargs.get('signal_name'),
                'instance': instance,
            }
        })

    if kwargs.get('signal_name').startswith('post_'):

        request.lizard_history[instance._lizard_history_hash].update({
            'post_copy': db_copy,
            'signal_name': kwargs.get('signal_name'),
        })


def process_request_handler(**kwargs):
    """
    Log any changes recorded on the request object.

    Some models are special, 

    """
    if not hasattr(request, 'lizard_history'):
        return

    logged_models = set()

    for action in request.lizard_history.values():

        if action['signal_name'] == 'post_save':

            obj = action['post_copy']
            if action['pre_copy'] is None:
                action_flag = utils.LIZARD_ADDITION
            else:
                action_flag = utils.LIZARD_CHANGE

        elif action['signal_name'] == 'post_delete':

            obj = action['pre_copy']
            action_flag = utils.LIZARD_DELETION

        else:
            continue

        # Custom handling starts here
        if isinstance(obj, AreaConfiguration):
            if AreaConfiguration in logged_models:
                continue  # Already logged the esf data
            else:
                object_repr = obj.area.ident
        elif isinstance(obj, WBCONFIGURATION_CLASSES):
            if logged_models.intersection(WBCONFIGURATION_CLASSES):
                continue  # Already logged the wbconfiguration data
            else:
                object_repr = obj.area.area.ident
        # Custom handling starts ends here
        else:
            object_repr=force_unicode(obj)
        
        change_message = utils.change_message(
            old_object=action['pre_copy'],
            new_object=action['post_copy'],
            instance=action['instance'],
        )

        # Don't log if nothing was changed.
        if change_message is None:
            return

        # Insert a log entry in django's admin log.
        LogEntry.objects.log_action(
            user_id=utils.user_pk(),
            content_type_id=utils.get_contenttype_id(obj),
            object_id=obj.pk,
            object_repr=object_repr,
            action_flag=action_flag,
            change_message=change_message,
        )

        logged_models.add(obj.__class__)
