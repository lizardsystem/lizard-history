# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.utils.encoding import force_unicode

from django.contrib.admin.models import LogEntry
from lizard_history import utils
from tls import request

HASH_ATTRIBUTE_NAME = '_lizard_history_hash'
HISTORY_ATTRIBUTE_NAME = 'lizard_history'


ESF_MODELS = (
    'lizard_esf.AreaConfiguration',
)

WBCONFIGURATION_MODELS = (
    'lizard_wbconfiguration.AreaConfiguration',
    'lizard_wbconfiguration.Structure',
    'lizard_wbconfiguration.Bucket',
)

def _add_m2m_to_obj_dict(obj):
    """
    Update obj.__dict__ with m2m items.

    This is meant as a temporary storage.
    """
    if obj is None:
        return

    print obj.waterbodies.all()

    for f in obj._meta._many_to_many():
        field_pk_queryset = getattr(obj, f.name).values_list('pk', flat=True)
        field_pk_list = list(field_pk_queryset)  # We must query right now.
        field_pk_list.sort()
        obj.__dict__.update({f.name: field_pk_list})

def _get_or_create_history(obj_hash):
    """
    Return history object from request if it is there.

    Install a history object on the request, if needed.
    """
    if hasattr(request, HISTORY_ATTRIBUTE_NAME):
        history = getattr(request, HISTORY_ATTRIBUTE_NAME)
        if hasattr
    else:
        history = {}
        setattr(request, HISTORY_ATTRIBUTE_NAME, history)


    


def db_handler(sender, instance, **kwargs):
    """
    Store old and new objects on the request.
    """

    is_raw = kwargs.get('raw')
    if (not request) or is_raw:
        return

    # Try to retrieve database version of instance.
    try:
        db_copy = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        db_copy = None

    if kwargs.get('signal_name').startswith('pre'):
        if hasattr(instance, HASH_ATTRIBUTE_NAME):
            getattr(request, HISTORY_ATTRIBUTE_NAME[])

        else:
            # Give object a unique id for identification in subsequent signals
            setattr(instance, HASH_ATTRIBUTE_NAME, utils.object_hash(instance))

            # Add m2m info
            _add_m2m_to_obj_dict(db_copy)

          
            # Store initial status of the object on the request.
            history.update({
                getattr(instance, HASH_ATTRIBUTE_NAME): {
                    'pre_copy': db_copy,
                    'instance': instance,
                    'signals': [kwargs.get('signal_name')],
                }
            })
    

    if kwargs.get('signal_name').startswith('post_'):
        # Store latest status of the object on the object
        history = getattr(request, HISTORY_ATTRIBUTE_NAME)
        history[getattr(instance, HASH_ATTRIBUTE_NAME)].update({
            'post_copy': db_copy,
        })


def process_request_handler(**kwargs):
    """
    Log any changes recorded on the request object.
    """
    if not hasattr(request, 'lizard_history'):
        return

    logged_models = set()

    for action in request.lizard_history.values():

        if action['signal_name'] == 'post_save':

            obj = action['post_copy']
            
            # Add m2m info
            _add_m2m_to_obj_dict(obj)

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
        if utils.is_object_of(obj, ESF_MODELS):
            if logged_models.intersection(ESF_MODELS):
                continue  # Already logged the esf data
            else:
                object_repr = obj.area.ident
        elif utils.is_object_of(obj, WBCONFIGURATION_MODELS):
            if logged_models.intersection(WBCONFIGURATION_MODELS):
                continue  # Already logged the wbconfiguration data
            else:
                object_repr = obj.area.area.ident
        # Custom handling starts ends here
        else:
            object_repr = force_unicode(obj)

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

        logged_models.add(utils.model_for_object(obj))
