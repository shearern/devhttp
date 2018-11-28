
from .Endpoint import Endpoint


class InternalError(Endpoint):
    '''500'''

    def __init__(self, e, extra_msg=None):
        self.__e = e
        self.__extra = extra_msg


    def respond(self, request):
        request.send_response(500)
        request.end_headers()
        request.wfile.write("""\
            <h1>{title}</h1>
            <div>{extra}</div>
            <div>{msg}</div>
            """.format(
                title = self.__e.__class__.__name__,
                extra = self.__extra or '',
                msg = str(self.__e)).encode('utf-8'))
