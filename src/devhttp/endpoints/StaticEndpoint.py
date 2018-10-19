
from .Endpoint import Endpoint


class StaticEndpoint(Endpoint):

    def __init__(self, asset):
        self.__file = asset


    def respond(self, request):

        # Return static content
        request.send_response(200)

        if self.__file.content_type is not None:
            request.send_header('Content-Type', self.__file.content_type)

        if self.__file.size is not None:
            request.send_header('Content-Length', str(self.__file.size))

        request.end_headers()

        request.wfile.write(self.__file.content)


