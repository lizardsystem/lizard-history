# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.utils.encoding import force_unicode

from django.contrib.admin.models import LogEntry
from lizard_history import utils
from tls import request

OBJECT_ATTRIBUTE = '_lizard_history_hash'
REQUEST_ATTRIBUTE = 'lizard_history'
PRE_COPY_KEY = 'pre_copy'
INSTANCE_KEY = 'instance'
SIGNALS_KEY = 'signals'


ESF_MODELS = (
    'lizard_esf.AreaConfiguration',
)

WBCONFIGURATION_MODELS = (
    'lizard_wbconfiguration.AreaConfiguration',
    'lizard_wbconfiguration.Structure',
    'lizard_wbconfiguration.Bucket',
)


def _get_or_create_history(obj):
    """
    Get or create the history dict for this object.

    Gets or sets OBJECT_ATTRIBUTE on object. Get or sets attribute
    REQUEST_ATTRIBUTE on request. Get or creates history item for object
    on request attribute and returns that.
    """
    if not hasattr(obj, OBJECT_ATTRIBUTE):
        setattr(obj, OBJECT_ATTRIBUTE, utils.object_hash(obj))
    obj_hash = getattr(obj, OBJECT_ATTRIBUTE)

    if not hasattr(request, REQUEST_ATTRIBUTE):
        setattr(request, REQUEST_ATTRIBUTE, {})
    history = getattr(request, REQUEST_ATTRIBUTE)

    if not obj_hash in history:
        history[obj_hash] = {SIGNALS_KEY: []}

    return history[obj_hash]


def _get_db_copy(obj):
    """
    Return database copy of obj.

    Update resulting objects __dict__ with m2m items.
    """
    # Get database copy
    model = obj.__class__
    try:
        db_copy = model.objects.get(pk=obj.pk)
    except model.DoesNotExist:
        return None

    # Add the m2m information
    for f in db_copy._meta._many_to_many():
        field_pk_qs = getattr(db_copy, f.name).values_list('pk', flat=True)
        field_pk_list = list(field_pk_qs)  # We must query right now.
        field_pk_list.sort()
        db_copy.__dict__.update({f.name: field_pk_list})

    return db_copy


def db_handler(sender, instance, signal_name, raw=None, **kwargs):
    """
    Store old and new objects on the request.
    """
    if raw or not request:
        return

    history = _get_or_create_history(instance)
    history[SIGNALS_KEY].append(signal_name)
    history[INSTANCE_KEY] = instance

    # Store initial status of the object on the request.
    if signal_name.startswith('pre_') and not PRE_COPY_KEY in history:
        history[PRE_COPY_KEY] = _get_db_copy(instance)


def process_request_handler(**kwargs):
    """
    Log any changes recorded on the request object.
    """
    if not hasattr(request, REQUEST_ATTRIBUTE):
        return
    try:
        actions = getattr(request, REQUEST_ATTRIBUTE).values()
    except AttributeError:
        return

    logged_models = set()

    for action in actions:

        pre_copy = action[PRE_COPY_KEY]
        post_copy = _get_db_copy(action[INSTANCE_KEY])
        last_signal = [s for s in action[SIGNALS_KEY]
                       if s in ('post_save', 'post_delete')][-1]

        if last_signal == 'post_save':
            obj = post_copy
            action_flag = (utils.LIZARD_CHANGE if pre_copy else
                           utils.LIZARD_ADDITION)
        elif last_signal == 'post_delete':
            obj = pre_copy
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
            old_object=pre_copy,
            new_object=post_copy,
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
