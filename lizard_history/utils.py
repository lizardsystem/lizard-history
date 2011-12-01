# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.db.models import Model
from mongoengine import Document

from django.utils import simplejson

from django.core.serializers import serialize

from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

from pymongo import json_util

from tls import request

import datetime
import difflib
import hashlib
import re


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


def _django_object_json(obj):
    """
    Return a dict representing the django model.

    Django's serializer works on iterables, here we want a single
    object. Therefore it gets loaded and dumped again.
    """
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


def _mongo_object_json(obj):
    """
    Return a dict representing a mongoengine document.
    """
    obj_mongo = obj.to_mongo()
    _clean_mongo_document_dict(obj_mongo)
    obj_json = simplejson.dumps(
        obj_mongo,
        default=json_util.default,
        indent=4,
    )
    return obj_json


def to_json(obj):
    """
    Return json corresponding to obj type.

    Currently supported are django and mongoengine models. If obj is None,
    return the empty string.
    """
    if obj is None:
        return ''
    elif isinstance(obj, Model):
        return _django_object_json(obj)
    elif isinstance(obj, Document):
        return _mongo_object_json(obj)
    else:
        raise NotImplementedError(
            'Only django and mongoengine models are currently implemented',
        )


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


def diff(str1, str2):
    """
    Return a context_diff with no context.
    """
    return list(difflib.context_diff(
        str1.splitlines(True),
        str2.splitlines(True),
        n=0,  # No context
    ))


def format_diff(diff):
    """
    Return a multiline diff string.
    """
    result = ''
    for line in diff[3:]:
        line = re.sub('^[!+-]', '', line)
        line = re.sub('^\*\*\*.*$', 'Removes:', line)
        line = re.sub('^--.*$', 'Adds:', line)
        result += line
    return result


def user_pk():
    """ Determine the user for this request."""
    if not request or isinstance(request.user, AnonymousUser):
        # Get the first superuser
        return User.objects.filter(is_superuser=True)[0].pk
    return request.user.pk
