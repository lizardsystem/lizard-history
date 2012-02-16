# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.db.models import Model
from mongoengine import Document

from django.utils import simplejson
from django.utils.translation import ugettext as _

from django.core.serializers import serialize

from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

from pymongo import json_util

from tls import request

import datetime
import difflib
import hashlib
import re

LIZARD_ADDITION = 4
LIZARD_CHANGE = 5
LIZARD_DELETION = 6


def user_pk():
    """ Determine the user for this request."""
    if isinstance(request.user, AnonymousUser):
        # Get the first superuser
        return User.objects.filter(is_superuser=True)[0].pk
    return request.user.pk


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


def _model_dict(obj):
    """
    Return a dict representing the Django model instance.

    Uses Django's serialization framework.
    """
    if obj is None:
        return {}

    obj_json = serialize(
        'json',
        [obj],
    )
    model_dict = simplejson.loads(obj_json)[0]['fields']
    print model_dict
    return model_dict


def _document_json_string(obj):
    """
    Return a json string representing a mongoengine document.
    """
    if obj is None:
        return ''

    obj_mongo = obj.to_mongo()
    _clean_mongo_document_dict(obj_mongo)
    obj_json = simplejson.dumps(
        obj_mongo,
        default=json_util.default,
        indent=4,
    )
    return obj_json


def get_contenttype_id(obj):
    """
    Return contenttype id or None.

    Currently supported are django models.
    """
    if isinstance(obj, Model):
        return ContentType.objects.get_for_model(obj).pk
    else:
        return None


def _clean_mongo_document_dict(obj):
    """
    Modify a dict recursively.

    Removes values whose key starts with '_' and replaces datetimes
    with strings.
    """
    for key, value in obj.items():
        if str(key).startswith('_'):
            del obj[key]
        elif isinstance(value, list):
            raise NotImplementedError('ListFields are not implemented yet')
        elif isinstance(value, dict):
            _clean_mongo_document_dict(value)
        elif isinstance(value, datetime.datetime):
            obj[key] = str(value)


def _text_diff(str1, str2):
    """
    Return a context_diff with no context.
    """
    return list(difflib.context_diff(
        str1.splitlines(True),
        str2.splitlines(True),
        n=0,  # No context
    ))


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



def _format_diff(diff):
    """
    Return a multiline diff string.
    """
    result = ''
    for line in diff[3:]:
        line = re.sub('^[!+-]', '', line)
        line = re.sub('^\*\*\*.*$', 'Removes:', line)
        line = re.sub('^--.*$', 'Adds:', line)
        if not line.endswith('\n'):
            # Make sure all lines end with a newline
            line += '\n'
        result += line
    result = result[:-1] # Remove last newline
    return result


def _model_diff(obj1, obj2):
    """
    Return diff for Django models or None objects
    """
    return _dict_diff(
        _model_dict(obj1),
        _model_dict(obj2),
    )


def _document_diff(obj1, obj2):
    """
    Return diff for Mongo documents or None objects
    """
    return _format_diff(_text_diff(
        _document_json_string(obj1),
        _document_json_string(obj2),
    ))
   

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
    elif _are_instance_or_none(obj1, obj2, Document):
        return _document_diff(obj1, obj2)
    elif obj1 is None and obj2 is None:
        return ''
    else:
        raise NotImplementedError(
            'Only django and mongoengine models '
            'are currently implemented',
        )

        
def change_message(obj1, obj2, summary):
    """
    Return a suitable change message
    """
    return simplejson.dumps(
        {
            'changes': _diff(obj1, obj2),
            'summary': summary,
        },
        indent=2
    )


def get_simple_history(obj):
    """ Get the history for a specific object """
    if obj is None:
        return None
    elif isinstance(obj, Model):

        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk

        try:
            created = LogEntry.objects.filter(
                object_id=object_id,
                content_type=content_type,
                action_flag=LIZARD_ADDITION
            ).latest('action_time')
            created_by = created.user
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
            modified_by = modified.user
            datetime_modified = modified.action_time
        except LogEntry.DoesNotExist:
            modified_by = None
            datetime_modified = None

        simple_history = {
            'datetime_created': str(datetime_created),
            'created_by': str(created_by),
            'datetime_modified': str(datetime_modified),
            'modified_by': str(modified_by),
        }
        return simple_history

    else:
        raise NotImplementedError(
            'Only django models are currently implemented',
        )

def _log_entry_to_dict(log_entry):
    """ Return a dict with selected info from log_entry """
    data = simplejson.loads(log_entry.change_message)
    changes = data['changes']
    summary = data['summary']

    action_flag_mapping = {
        LIZARD_CHANGE: _('Changed'),
        LIZARD_ADDITION: _('Created'),
        LIZARD_DELETION: _('Deleted'),
    }

    result = {
        'action': action_flag_mapping[log_entry.action_flag],
        'user': str(log_entry.user),
        'datetime': str(log_entry.action_time),
        'summary': summary,
        'log_entry_id': log_entry.pk,
        'changes': dict([(k, v['new'])
                         for k, v in changes.items()]),
    }

    return result


def get_history(obj=None, log_entry_id=None):
    """
    Return full history for obj or changes for log_entry_id
    """
    if log_entry_id:
        log_entry = LogEntry.objects.get(pk=log_entry_id)
        return _log_entry_to_dict(log_entry)

    if isinstance(obj, Model):

        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk

        entries = LogEntry.objects.filter(
            object_id=object_id,
            content_type=content_type,
            action_flag__in=[LIZARD_ADDITION, LIZARD_CHANGE, LIZARD_DELETION],
        )

        return [_log_entry_to_dict(l) for l in entries]

    raise NotImplementedError(
        'Only django models are currently implemented',
    )
