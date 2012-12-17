# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.db.models import Model
from django.http import HttpRequest

from django.utils import simplejson
from django.utils.translation import ugettext as _

from django.core.serializers import serialize
from django.core.serializers.json import DateTimeAwareJSONEncoder

from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

from tls import request as tls_request
from werkzeug.local import Local, release_local
from lizard_history.signals import ops_done
from django_load.core import load_object

import datetime
import hashlib


WBCONFIGURATION_MODELS = (
    'lizard_wbconfiguration.AreaConfiguration',
    'lizard_wbconfiguration.Structure',
    'lizard_wbconfiguration.Bucket',
)

LIZARD_ADDITION = 4
LIZARD_CHANGE = 5
LIZARD_DELETION = 6

_local = Local()
fake_request = _local('fake_request')


def active_request():
    return tls_request or fake_request


def start_fake_request(**kwargs):
    """
    Set a fake request.

    It will be used by lizard_history if there is no real request. Any
    kwargs will be set as attributes on the fake request.
    """
    fake_request = HttpRequest()
    for k, v in kwargs.items():
        setattr(fake_request, k, v)
    _local.fake_request = fake_request


def end_fake_request():
    """
    Start lizard_history machinery to log changes and remove the
    fake_request from the thread.
    """
    ops_done.send(None)
    release_local(_local)


def user_pk():
    """ Determine the user for this request."""
    user = active_request().user
    if isinstance(user, AnonymousUser) or not user:
        # Get the first superuser
        return User.objects.filter(is_superuser=True)[0].pk
    return user.pk


def object_hash(obj, use_time=True):
    """
    Return sha1 hash for obj.
    """
    sha1 = hashlib.sha1()
    sha1.update(obj.__class__.__module__)
    sha1.update(obj.__class__.__name__)
    sha1.update(str(obj.pk))
    if use_time:
        sha1.update(str(datetime.datetime.now()))

    return sha1.hexdigest()


def model_for_object(obj):
    """
    Return model path in 'app_label.object_name' style
    """
    return obj._meta.app_label + '.' + obj._meta.object_name


def is_object_of(obj, model):
    """
    Return if objects class info matches at least one of mod_and_class.
    """
    if isinstance(model, str):
        models = [model]
    else:
        models = model

    for m in models:
        if m == model_for_object(obj):
            return True

    return False


def _model_dict(obj):
    """
    Return a dict representing the Django model instance.

    Uses Django's serialization framework.
    """
    if obj is None:
        return {}

    # Unfortunately, the presave trigger comes before django's own
    # full cleaning, so serialize fails if datetime is a string.
    # obj.full_clean()  # May be no problem since logging now afterwards.
    obj_json = serialize(
        'json',
        [obj],
    )
    model_dict = simplejson.loads(obj_json)[0]['fields']
    return model_dict


def _model_dict_based_on_dict(obj):
    """
    Return a dict representing the Django model instance.

    Uses objects __dict__ attribute, to include fields from parent models.
    """
    if obj is None:
        return {}

    model_dict = {}

    for k, v in obj.__dict__.items():
        if not k.startswith('_'):
            model_dict[k] = unicode(v)  # Mainly to get rid of datetimes

    return model_dict


def get_contenttype_id(obj):
    """
    Return contenttype id or None.

    Currently supported are django models.
    """
    if isinstance(obj, Model):
        return ContentType.objects.get_for_model(obj).pk
    else:
        return None


def _dict_diff(dict1, dict2):
    """
    Return a dict representing the difference.

    Assumes two flat dicts.
    """
    keys = set(dict1.keys()) | set(dict2.keys())
    result = {}
    for k in keys:
        if not dict1.get(k) == dict2.get(k):
            result[k] = {
                'old': dict1.get(k),
                'new': dict2.get(k),
            }

    return result


def _model_diff(obj1, obj2):
    """
    Return diff for Django models or None objects
    """
    return _dict_diff(
        _model_dict_based_on_dict(obj1),
        _model_dict_based_on_dict(obj2),
    )


def _are_instance_or_none(obj1, obj2, klass):
    """
    Return True if one or both objects are instance of klass
    and the other is None.
    """
    return (isinstance(obj1, klass) and isinstance(obj2, klass) or
            isinstance(obj1, klass) and obj2 is None or
            isinstance(obj2, klass) and obj1 is None)


def _diff(obj1, obj2):
    """
    Return diff object corresponding to object type.
    """
    if _are_instance_or_none(obj1, obj2, Model):
        return _model_diff(obj1, obj2)
    elif obj1 is None and obj2 is None:
        return {}


def _api_object(obj, view):
    """
    Return data if view is a base_api subclass
    """
    return {
        'api_object': {
            'data': view().get_object_for_api(
                obj,
                include_geom=True,
                flat=False,
            ),
            'success': True,
        }
    }


def _other_object(obj, view):
    """
    Return data for general get request on view.
    """
    # Our view expects a request, so let's make one.
    
    view_request = HttpRequest()
    view_request.user = active_request().user
    view_request.GET = view_request.GET.copy()  # Make request mutable.
    view_request.GET.update(object_id=obj.area.ident)

    return {
        'tree': view().get(view_request)
    }


def _custom_extras(obj):
    """
    Return custom properties to save in history.
    """
    if not hasattr(obj, 'HISTORY_DATA_VIEW'):
        return {}
    view = load_object(obj.HISTORY_DATA_VIEW)

    view.user = active_request().user  # For the wbconfiguration to work...

    if hasattr(view, 'get_object_for_api'):
        return _api_object(obj, view)

    return _other_object(obj, view)


def change_message(old_object, new_object, instance):
    """
    Return a suitable change message.
    """
    message_object = {
        'changes': _diff(old_object, new_object),
    }

    if hasattr(instance, 'lizard_history_summary'):
        message_object.update(summary=instance.lizard_history_summary)

    message_object.update(_custom_extras(new_object))

    # If there are no changes, we need no log.
    if message_object == {'changes': {}}:
        return None

    return simplejson.dumps(
        message_object,
        cls=DateTimeAwareJSONEncoder,
    )


def get_simple_history(obj):
    """ Get the history for a specific object """
    if obj is None:
        return None

    content_type = ContentType.objects.get_for_model(obj)
    object_id = obj.pk

    try:
        created = LogEntry.objects.filter(
            object_id=object_id,
            content_type=content_type,
            action_flag=LIZARD_ADDITION
        ).latest('action_time')
        created_by = created.user.get_full_name() or created.user
        datetime_created = created.action_time
    except LogEntry.DoesNotExist:
        created_by = None
        datetime_created = None

    try:
        modified = LogEntry.objects.filter(
            object_id=object_id,
            content_type=content_type,
            action_flag=LIZARD_CHANGE
        ).latest('action_time')
        modified_by = modified.user.get_full_name() or modified.user
        datetime_modified = modified.action_time
    except LogEntry.DoesNotExist:
        modified_by = None
        datetime_modified = None

    simple_history = {
        'datetime_created': datetime_created,
        'created_by': created_by,
        'datetime_modified': datetime_modified,
        'modified_by': modified_by,
    }

    return simple_history


def _log_entry_to_dict(log_entry, include_data=False):
    """ Return a dict with selected info from log_entry """
    data = simplejson.loads(log_entry.change_message)

    action_flag_mapping = {
        LIZARD_CHANGE: _('Changed'),
        LIZARD_ADDITION: _('Created'),
        LIZARD_DELETION: _('Deleted'),
    }

    result = {
        'action': action_flag_mapping[log_entry.action_flag],
        'user': str(log_entry.user),
        'datetime': str(log_entry.action_time),
        'log_entry_id': log_entry.pk,
        'object_repr': log_entry.object_repr,
    }

    # Include summary regardless of include_data argument
    result.update(summary=data.get('summary', ''))

    if include_data:
        result.update(data)

    return result


def get_history(obj=None, log_entry_id=None, include_data=True):
    """
    Return full history for obj or changes for log_entry_id
    """
    if log_entry_id:
        log_entry = LogEntry.objects.get(pk=log_entry_id)
        return _log_entry_to_dict(log_entry, include_data=include_data)

    content_type = ContentType.objects.get_for_model(obj)
    object_id = obj.pk

    entries = LogEntry.objects.filter(
        object_id=object_id,
        content_type=content_type,
        action_flag__in=[LIZARD_ADDITION, LIZARD_CHANGE, LIZARD_DELETION],
    )

    return [_log_entry_to_dict(l) for l in entries]


def get_specific_history(models, area):
    """
    Return specific history list corresponding to models and area.
    """
    content_types = map(
        ContentType.objects.get_for_model,
        models,
    )

    # Works for objects where complete log is stored in single logentry
    # with area_ident in the object_repr field.
    entries = LogEntry.objects.filter(
        content_type__in=content_types,
        object_repr=area.ident,
    )

    return [_log_entry_to_dict(l) for l in entries]
