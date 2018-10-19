

from .Endpoint import Endpoint
from .InternalError import InternalError


class ThreadedServerWrapper:
    '''Wraps access to server attributes in a thread safe method'''

    def __init__(self, server):
        self.__server = server


class DynamicEndpoint(Endpoint):

    def __init__(self, callable, server, assets, content_type):
        '''

        :param callable: The callable to generate the content for the client
        :param server: The DevelopmentHttpServer object
        :param assets: The assets container
        '''
        self.__view_callable = callable
        self.__server = ThreadedServerWrapper(server)
        self.__assets = assets
        self.__content_type = content_type


    def respond(self, request):

        # Call callable to generate content
        try:
            content = self.__view_callable(
                request=request,
                server=self.__server,
                assets=self.__assets)
        except Exception as e:
            InternalError(e, "Failed to call dynamic content generator: %s()" % (
                self.__view_callable.__name__)).respond(request)
            return

        # Encode to binary
        if content.__class__ is str:
            content = content.encode('utf-8')


        # Return content headers
        request.send_response(200)

        if self.__content_type is not None:
            request.send_header('Content-Type', self.__content_type)

        request.send_header('Content-Length', len(content))

        request.end_headers()

        request.wfile.write(content)
