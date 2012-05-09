# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from tls import TLSRequestMiddleware
from lizard_history.signals import ops_done

class HistoryMiddleware(object):
    
    def process_response(self, request, response):
        ops_done.send(None)
        return response

    def process_exception(self, request, exception):
        ops_done.send(None)
