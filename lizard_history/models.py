# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from mongoengine.signals import pre_save as mongo_pre_save
from mongoengine.signals import post_save as mongo_post_save
from mongoengine.signals import post_delete as mongo_post_delete

from django.db.models.signals import pre_save as django_pre_save
#from django.db.models.signals import post_save as django_post_save
from django.db.models.signals import post_delete as django_post_delete
from django.db.models import Model

from django.dispatch import receiver

from django.utils.encoding import force_unicode
from django.utils import simplejson

from django.core.serializers import serialize

from django.contrib.contenttypes.models import ContentType

from django.contrib.sessions.models import Session

from django.contrib.admin.models import LogEntry
from django.contrib.admin.models import ADDITION
from django.contrib.admin.models import CHANGE
from django.contrib.admin.models import DELETION

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

from pymongo import json_util
from tls import request

import datetime
import difflib
import logging
import pprint
import re

import lizard_history.configchecker
lizard_history.configchecker  # Pyflakes...

logger = logging.getLogger()

# Django models not to include in history tracking
EXCLUDED_MODELS = (
    Session,
)

# Mongoengin documents not to include in history tracking
EXCLUDED_DOCUMENTS = ()


def _clean_mongo_document_dict(obj):
    """
    Remove items whose key starts with '_' recursively
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


def _json_diff(json1, json2):
    """
    Return a multiline diff string.
    """
    context_diff = list(difflib.context_diff(
        json1.splitlines(True),
        json2.splitlines(True),
        n=0,  # No context lines
    ))
    result = ''
    for line in context_diff[3:]:
        line = re.sub('^[!+-]', '', line)
        line = re.sub('^\*\*\*.*$','Removes:', line)
        line = re.sub('^--.*$','Adds:', line)
        result += line
    return result[:-1]


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
        simplejson.loads(obj_json)[0],
        indent=4,
    )
    return single_obj_json


def _mongo_document_json(obj):
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


def _user_pk():
    """ Determine the user for this request."""
    if not request or isinstance(request.user, AnonymousUser):
        # Get the first superuser
        return User.objects.filter(is_superuser=True)[0].pk
    return request.user.pk


@receiver(django_pre_save)
def django_pre_save_handler(sender, instance, raw, **kwargs):
    """
    Log a change or addition of a django model in the logentry.
    """
    if raw:
        # A fixture is loaded, may be we don't want to log
        # any fixtures loaded?
        return

    if sender == LogEntry:
        # We must prevent LogEntries to trigger new LogEntries to be saved.
        return

    if sender in EXCLUDED_MODELS:
        return

    # Determine the type of action, and an appropriate change message
    try:
        original = sender.objects.get(pk=instance.pk)
        action_flag = CHANGE
        change_message = _json_diff(
            _django_object_json(original),
            _django_object_json(instance),
        )
    except sender.DoesNotExist:
        action_flag = ADDITION
        change_message = _json_diff(
            '',
            _django_object_json(instance),
        )

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=_user_pk(),
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=force_unicode(instance),
        action_flag=action_flag,
        change_message=change_message,
    )


@receiver(django_post_delete)
def post_delete_handler(sender, instance, **kwargs):
    """
    Put a delete entry in the logentry.
    """
    if sender in EXCLUDED_MODELS:
        return

    # Set action_flag and change message
    action_flag = DELETION
    change_message = _json_diff(
        _django_object_json(instance),
        '',
    )

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=_user_pk(),
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=force_unicode(instance),
        action_flag=action_flag,
        change_message=change_message,
    )


@receiver(mongo_pre_save)
def mongo_pre_save_handler(sender, document, **kwargs):
    """
    Store the original document on the request if it exists.
    """
    if sender in EXCLUDED_DOCUMENTS:
        return
    if document.pk is not None:
        try:
            original = sender.objects.get(pk=document.pk)
            if not hasattr(request, 'lizard_history'):
                request.lizard_history = [(original, document)]
            else:
                request.lizard_history.append((original, document))
            return
        except sender.DoesNotExist:
            return


@receiver(mongo_post_save)
def mongo_post_save_handler(sender, document, created):
    """
    Log a change or addition of a mongoengine document in the logentry.

    Beware that created is only True if no pk was set before saving.
    """
    if sender in EXCLUDED_DOCUMENTS:
        return
    # Determine the type of action, and an appropriate change message
    if created:
        original_document, pre_save_document = request.lizard_history.pop()
        if pre_save_document != document:
            raise Exception('A serious error happened in the lizard history app')
        
        # Mongoengine tends to save referred objects as well,
        # but if they are not changed, this should not be logged either.
        if not pre_save_document._get_changed_fields():
            return

        action_flag = CHANGE
        change_message = _json_diff(
            _mongo_document_json(original),
            _mongo_document_json(document),
        )
        
    else:

        action_flag = ADDITION
        change_message = _json_diff(
            '',
            _mongo_document_json(document),
        )

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=_user_pk(),
        content_type_id=None,
        object_id=document.pk,
        object_repr=force_unicode(document),
        action_flag=action_flag,
        change_message=change_message,
    )


@receiver(mongo_post_delete)
def mongo_post_delete_handler(sender, document,*args,**kwargs):
    """
    Put a delete entry in the logentry.
    """
    if sender in EXCLUDED_MODELS:
        return

    # Set action_flag and change message
    action_flag = DELETION
    change_message = _json_diff(
        _mongo_document_json(document),
        '',
    )

    # Insert a log entry in django's admin log.
    LogEntry.objects.log_action(
        user_id=_user_pk(),
        content_type_id=None,
        object_id=document.pk,
        object_repr=force_unicode(document),
        action_flag=action_flag,
        change_message=change_message,
    )
