import os
import logging
from mimetypes import guess_type
from http.server import HTTPServer
from socketserver import ThreadingMixIn

from .AssetFile import AssetFile
from .DevelopmentRequestHandler import DevelopmentRequestHandler

from .endpoints import StaticEndpoint, DynamicEndpoint, NotFoundEndpoint

from .utils import find, normalize_url

class ThreadedHTTPListener(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class DevelopmentHttpServer:
    '''A quick and dirty HTTP server'''

    def __init__(self):

        # Store static and dynamic endpoints in one collection
        self.__endpoints = dict()

        # Store assets in their own container
        self.__assets = dict()


    def get_endpoint(self, url_path, method):
        '''
        Called by handler to get the response contents

        :param url: Path portion of URL
        :param method: GET, POST, etc.
        '''

        url_path = normalize_url(url_path)

        if url_path in self.__endpoints:
            return self.__endpoints[url_path]

        return NotFoundEndpoint()


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
        url = normalize_url(url)

        # Make sure path is unique
        if url in self.__endpoints:
            logging.getLogger(__name__).warning("Duplicate path provided: " + url)

        # Save
        file = AssetFile(
            asset_type = AssetFile.ASSET,
            name = url,
            content_type = content_type,
            path = path,
            size = size)
        self.__endpoints[url] = StaticEndpoint(asset = file)


    def add_multiple_static(self, url_prefix, path, filter_paths=None):
        '''
        Add multiple static files that can be served

        :param url_prefix:
            Prefix to apply to all files included
        :param path:
            Path to directory to `search for files under
        :param filter_paths:
            method to filter which paths to include
        '''

        url_prefix = normalize_url(url_prefix)
        if url_prefix != '' and not url_prefix.endswith('/'):
            url_prefix += '/'

        for filepath in find(path):
            if filter_paths is None or filter_paths(filepath):
                self.add_static(
                    url = url_prefix + filepath,
                    path = os.path.join(path, filepath))


    def add_asset(self, name, path):
        '''
        Add an asset that can be used by the dynamic content generators

        :param name:
            Name to refer to the file when retrieving
        :param path:
            Path to the file on disk
        '''

        # Make sure path is unique
        if name in self.__assets:
            logging.getLogger(__name__).warning("Duplicate asset key: " + name)

        # Save
        self.__assets[name] = AssetFile(
            asset_type = AssetFile.ASSET,
            name = name,
            content_type = None,
            path = path,
            size = None)


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

        url = normalize_url(url)

        # Make sure path is unique
        if url in self.__endpoints:
            raise KeyError("Path already defined for a view")

        # Interpret content type
        if '/' in content_type:
            pass
        else:
            # Allow caller to specify a filename, or just an extension
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
        self.__endpoints[url] = DynamicEndpoint(
            callable = callable,
            server = self,
            assets = self.__assets,
            content_type = content_type)


    def serve_forever(self, ip, port):
        '''Listted for HTTP requests as serve content from this server'''
        http_server = ThreadedHTTPListener((ip, port), DevelopmentRequestHandler)
        http_server.development_http_server = self
        http_server.serve_forever()

