from abc import ABC, abstractmethod

class Endpoint(ABC):
    '''Something that can be requested from the server'''

    @abstractmethod
    def respond(self, request):
        '''
        Called to respond to a request

        This will be called across server threads

        :param request:

            The DevelopmentRequestHandler holding the request details and providing
            the mechanisms to respond to the request.

            Available attributes
            --------------------
            .client_address = (host, port) referring to the client’s address.
            .server = Contains the server instance (DevelopmentHttpServer)
            .close_connection = indicating if another request may be expected,
                                or if the connection should be shut down.
            .requestline = HTTP request line. The terminating CRLF is stripped.
            .command = Contains the command (request type). For example, 'GET'.
            .path = Contains the request path.
            .headers = Headers in the HTTP request
            .rfile = input stream, ready to read from the start of the optional input data.
            .wfile = output stream for writing a response back to the client
            responses = mapping of error code integers to (shortmessage, longmessage)

            Available methods
            -----------------
            .send_error(code, message=None, explain=None)
                Sends and logs a complete error reply to the client
            .send_response(code, message=None)
                Adds a response header to the headers buffer and logs the accepted request.
            .send_header(keyword, value)
                Adds the HTTP header to an internal buffer which will be written to the
                output stream when either end_headers() or flush_headers() is invoked.
            .send_response_only(code, message=None)
                Sends the response header only, used for the purposes when 100 Continue
                response is sent by the server to the client.
                The headers not buffered and sent directly the output stream.
            .end_headers()
                Adds a blank line (indicating the end of the HTTP headers in the response)
            .flush_headers()
                Finally send the headers to the output stream and flush the internal headers
                buffer.
            .log_request(code='-', size='-')
                Logs an accepted (successful) request
            .log_error(...)
                Logs an error when a request cannot be fulfilled.
            .address_string()
                Returns the client address.
        '''
