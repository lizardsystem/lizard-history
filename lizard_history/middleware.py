# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from tls import TLSRequestMiddleware
from lizard_history.signals import ops_done

class HistoryMiddleware(TLSRequestMiddleware):
    
    def process_response(self, request, response):
        ops_done.send(None)
        return super(
            HistoryMiddleware, self,
        ).process_response(
            request, response,
        )

    def process_exception(self, request, exception):
        ops_done.send(None)
        return super(
            HistoryMiddleware, self,
        ).process_exception(
            request, exception,
        )


