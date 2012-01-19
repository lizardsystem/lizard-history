# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.db.models import Model
from mongoengine import Document

from django.utils import simplejson

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


def _model_json(obj):
    """
    Return a dict representing the django model.

    Django's serializer works on iterables, here we want a single
    object. Therefore it gets loaded and dumped again.
    """
    if obj is None:
        return ''

    obj_json = serialize(
        'json',
        [obj],
        indent=4,
    )
    single_obj_json = simplejson.dumps(
        simplejson.loads(obj_json)[0]['fields'],
        indent=4,
    )
    return single_obj_json


def _document_json(obj):
    """
    Return a dict representing a mongoengine document.
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
    return _format_diff(_text_diff(
        _model_json(obj1),
        _model_json(obj2),
    ))


def _document_diff(obj1, obj2):
    """
    Return diff for Mongo documents or None objects
    """
    return _format_diff(_text_diff(
        _document_json(obj1),
        _document_json(obj2),
    ))
   

def _are_instance_or_none(obj1, obj2, klass):
    """
    Return True if one or both objects are instance of klass
    and the other is None.
    """
    return (isinstance(obj1, klass) and isinstance(obj2, klass) or
            isinstance(obj1, klass) and obj2 is None or
            isinstance(obj2, klass) and obj1 is None)
            

def diff(obj1, obj2):
    """
    Return diff string corresponding to object type.
    """
    if _are_instance_or_none(obj1, obj2, Model):
        print _model_diff(obj1, obj2)
        return _model_diff(obj1, obj2)
    elif _are_instance_or_none(obj1, obj2, Document):
        print _document_diff(obj1, obj2)
        return _document_diff(obj1, obj2)
    elif obj1 is None and obj2 is None:
        return ''
    else:
        raise NotImplementedError(
            'Only django and mongoengine models '
            'are currently implemented',
        )


def get_history(obj):
    """ Get the history for a specific object """
    if obj is None:
        return None
    elif isinstance(obj, Model):
        content_type = ContentType.objects.get_for_model(obj)
        object_id = obj.pk
        hist = LogEntry.objects.filter(
            content_type=content_type,
            object_id=object_id,
        )
        print hist
        return 'django!'

    elif isinstance(obj, Document):
        return 'mongo!'
    else:
        raise NotImplementedError(
            'Only django and mongoengine models are currently implemented',
        )
