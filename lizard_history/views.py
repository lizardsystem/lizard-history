# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from djangorestframework.response import Response
from djangorestframework.views import View
from djangorestframework import status
from lizard_history import utils


class ApiObjectView(View):
    """
    Show a historic api object stored in the admin log
    """
    def get(self, request, log_entry_id):
        if request.user.is_anonymous():
            return Response(status.HTTP_403_FORBIDDEN)
        history = utils.get_history(
            log_entry_id=log_entry_id,
        )

        if 'api_object' in history:
            return history['api_object']

        return Response(status.HTTP_404_NOT_FOUND)

        
class OtherObjectView(View):
    """
    Show a historic other object stored in the admin log
    """
    def get(self, request, log_entry_id):
        if request.user.is_anonymous():
            return Response(status.HTTP_403_FORBIDDEN)
        history = utils.get_history(
            log_entry_id=log_entry_id,
        )

        if 'tree' in history:
            return history['tree']

        return Response(status.HTTP_404_NOT_FOUND)


class AreaObjectConfigurationView(View):
    """
    Show archive data for area object configuration.
    Supply an object_type with the request.
    """
    def get(self, request, log_entry_id):

        if request.user.is_anonymous():
            return Response(status.HTTP_403_FORBIDDEN)

        history = utils.get_history(
            log_entry_id=log_entry_id,
        )
        try:
            area_object_type = request.GET['area_object_type']
            return history[area_object_type.lower()]
        except KeyError:
            return Response(status.HTTP_404_NOT_FOUND)


class AreaConfigurationView(View):
    """
    Show archive data for area configuration.
    Supply a grid_name with the request.
    """
    def get(self, request, log_entry_id):

        if request.user.is_anonymous():
            return Response(status.HTTP_403_FORBIDDEN)

        history = utils.get_history(
            log_entry_id=log_entry_id,
        )

        try:
            grid_name = request.GET['grid_name']
            return history[grid_name.lower()]
        except KeyError:
            return Response(status.HTTP_404_NOT_FOUND)
