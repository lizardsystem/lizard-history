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
