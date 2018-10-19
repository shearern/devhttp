
from .Endpoint import Endpoint


class NotFoundEndpoint(Endpoint):
    '''404'''

    def respond(self, request):
        request.send_response(404)
        request.end_headers()
        request.wfile.write("<h1>404 Not Found</h1>".encode('utf-8'))
