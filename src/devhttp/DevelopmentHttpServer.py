import os
import logging
from mimetypes import guess_type
from http.server import HTTPServer
from socketserver import ThreadingMixIn

from .StaticFiles import StaticFiles
from .StaticFile import StaticFile
from .DevelopmentRequestHandler import DevelopmentRequestHandler
from .ThreadedServerWrapper import ThreadedServerWrapper

from . import responses

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class DevelopmentHttpServer:
    '''A quick and dirty HTTP server'''

    def __init__(self):

        # Container to store statics and assets added to the server
        self.__assets = StaticFiles()

        # Libraries of statics and assets loaded by load_assets_module()
        self.__asset_libs = list()

        # Dynamic content generators
        self.__views = dict()


    def get_response(self, url, method):
        '''
        Called by handler to get the response contents

        :param url: Path portion of URL
        :param method: GET, POST, etc.
        '''
        if method == 'GET':

            if self.__assets.has(url):
                return responses.StaticFileResponse(self.__assets.get(url))

            if url in self.__views:
                callable, content_type = self.__views[url]
                rendered = callable(None, None, None) # TODO: Setup parms
                return responses.DynamicResponse(rendered, content_type)

        raise Exception("Don't know how to respond to %s:%s" % (method, url))


    def add_static(self, url, path, content_type=None, size=None):
        '''
        Add a static file that can be served by the server

        :param url:
            The URL that represents this file to the browser

            The URL matches the path portion of the URL (not the server, port,
            or parameters)
        :param path:
            Path to the file to serve up
        :param content_type:
            Content type to provide with the content
        :param size:
            Size of the content in bytes
        '''

        # Make sure path is unique
        if self.__assets.has(url):
            logging.getLogger(__name__).warning("Duplicate path provided: " + url)

        # Make sure file exists
        if not os.path.exists(path):
            raise NameError("File doesn't exist: %s" % (path))

        # Guess content type from filename
        if content_type is None:
            content_type = guess_type(path)
            if content_type[0] is None:
                logging.getLogger(__name__).warning(
                    "Can't determine mimetype for %s" % (path))
            else:
                content_type = content_type[0]

        # Get file size
        if size is None:
            size = os.path.getsize(path)

        # Save
        self.__assets.add(StaticFile(
            asset_type = StaticFile.ASSET,
            name = url,
            content_type = content_type,
            path = path,
            size = size
        ))


    def add_asset(self, name, path):
        '''
        Add an asset that can be used by the dynamic content generators

        :param name:
            Name to refer to the file when retrieving
        :param path:
            Path to the file on disk
        '''

        # Make sure path is unique
        if self.__assets.has(name):
            logging.getLogger(__name__).warning("Duplicate asset key: " + name)

        # Save
        self.__assets.add(StaticFile(
            asset_type = StaticFile.ASSET,
            name = name,
            content_type = None,
            path = path,
            size = None
        ))


    def add_dynamic(self, url, callable, content_type):
        '''
        Add a dynamic content generating method callable

        The callable will receive the parameters:
            func(request, server, assets)

        :param url:
            The URL that represents this file to the browser
        :param callable:
            The callable to generate the content to return to the browser

            It's important to note that the callable can be invoked multiple times
            in parallel since the HTTP server is threaded.  It must be thread safe.
            However, the dynamic code will be passed a reference to the server which
            can be assumed thread safe due to the ServerWrapper which protects the
            Server class attributes with a thread lock.  Therfore, store your shared
            state in the server class (inherited from DevelopmentHttpServer).
        :param content_type:
            Either a content type to return, or a filename to guess content type from
        '''

        # Make sure path is unique
        if url in self.__views:
            raise KeyError("Path already defined for a view")

        # Interpret content type
        if '/' in content_type:
            pass
        else:
            filename = content_type
            if filename.startswith('.'):
                filename = 'file' + filename
            content_type = guess_type(filename)
            if content_type[0] is None:
                logging.getLogger(__name__).warning(
                    "Can't determine mimetype for %s" % (filename))
            else:
                content_type = content_type[0]

        # Register callable
        self.__views[url] = (callable, content_type)


    def serve_forever(self, ip, port):
        '''Listted for HTTP requests as serve content from this server'''
        http_server = ThreadedHTTPServer((ip, port), DevelopmentRequestHandler)
        http_server.development_http_server = self
        http_server.serve_forever()

