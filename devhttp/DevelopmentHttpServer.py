import os
import logging
from threading import RLock
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from mimetypes import guess_type
from textwrap import dedent
from tempfile import TemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED
from base64 import b64encode
from io import BytesIO
import json

from .AssetFile import AssetFile, SavedAssetFile
from .DevelopmentRequestHandler import DevelopmentRequestHandler

from .endpoints import StaticEndpoint, DynamicEndpoint, NotFoundEndpoint

from .utils import find, normalize_url, SharedZipFileReader

class ThreadedHTTPListener(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class DevelopmentHttpServer:
    '''A quick and dirty HTTP server'''

    def __init__(self):

        # Store static and dynamic endpoints in one collection
        self.__endpoints = dict()

        # Store assets in their own container
        self.__assets = dict()

        # Redirects or URL aliases  [url]: redirect_to_url
        self.__redirects = dict()

        # Lock to protect concurrent access across handler threads
        self.lock = RLock()


    def get_endpoint(self, url_path, method):
        '''
        Called by handler to get the response contents

        :param url: Path portion of URL
        :param method: GET, POST, etc.
        '''

        url_path = normalize_url(url_path)

        with self.lock:
            if url_path in self.__redirects:
                url_path = self.__redirects[url_path]

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

        with self.lock:

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

        with self.lock:

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


    def add_dynamic(self, url, callable, content_type=None, autolock=True):
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
        :param autolock:
            If True, then will aquire server.lock before calling dynamic code generator.
            This blocks all other requests (static and dynamic), so if you want to lock
            manually on a long-running request, set to false and lock in your view with:
                with server.lock:
                    # do stuff
        '''

        url = normalize_url(url)

        with self.lock:

            # Make sure path is unique
            if url in self.__endpoints:
                raise KeyError("Path already defined for a view")

            # Interpret content type
            if content_type is None:
                content_type = os.path.basename(url)
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
                content_type = content_type,
                autolock = autolock)


    def redirect(self, from_url, to_url):
        '''
        Record a redirect (a URL alias) to allow content to be accessed under multiple urls

        Typical usage:
            .redirect('', 'index.html')

        :param from_url:
            URL to respond to
        :param to_url:
            Existing endpoint URL to repond to from_url
        '''

        from_url = normalize_url(from_url)
        to_url = normalize_url(to_url)

        with self.lock:

            if to_url not in self.__endpoints:
                raise KeyError("No endpoint defined for url %s" % (to_url))

            self.__redirects[from_url] = to_url


    def serve_forever(self, ip, port):
        '''Listted for HTTP requests as serve content from this server'''
        http_server = ThreadedHTTPListener((ip, port), DevelopmentRequestHandler)
        http_server.development_http_server = self
        http_server.serve_forever()


    def save_assets_module(self, path, var_name='STATIC_DATA'):
        '''
        Create a Python module that contains all statics and assets

        to be loaded by load_assets_module()

        :param path: Path to module to write
        :param var_name: Name of variable holding the data in the module
        '''

        # Begin manifest
        manifest = {
            'endpoints': list(),
            'assets': list(),
        }

        # Zip up the files
        zip_fh = TemporaryFile(suffix='.zip')
        with ZipFile(zip_fh, mode='w') as zip:

            # Statics
            i = 0
            for url, endpoint in self.__endpoints.items():

                try:
                    asset = endpoint.asset_file
                except AttributeError:
                    continue

                i += 1
                filename = 'static.%d.dat' % (i)

                manifest['endpoints'].append({
                    'url':      url,
                    'asset':    asset.save_metadata(),
                    'filename': filename,
                })

                zip.writestr(filename, asset.content, ZIP_DEFLATED)


            # Assets
            i = 0
            for name, asset in self.__assets.items():

                i += 1
                filename = 'asset.%d.dat' % (i)

                manifest['assets'].append({
                    'name':     name,
                    'asset':    asset.save_metadata(),
                    'filename': filename,
                })

                zip.writestr(filename, asset.content, ZIP_DEFLATED)

            # Save manifest file
            zip.writestr('manifest.json', json.dumps(manifest, indent=4), ZIP_DEFLATED)

        # Encapsulate data into a Python Module
        zip_fh.seek(0)
        b64zip = b64encode(zip_fh.read()).decode('ascii')

        chunk_size = 100
        b64zip = [b64zip[i:i+chunk_size] for i in range(0, len(b64zip), chunk_size)]

        # Write out module
        with open(path, 'wt') as fh:
            fh.write(dedent("""\
                from base64 import b64decode
                
                {name} = b64decode('''
                {b64zip}
                    '''.strip().replace("\\n", ""))
                """).format(
                    name = var_name,
                    b64zip = "\n".join(['    ' + line for line in b64zip])
                ))
        # TODO: Remove old zip line


    def load_assets_module(self, assets_data):
        '''
        Load back statics and assets encoded into a Python module

        :param assets_data: BytesIO
            Asset data generated by save_assets_module()

        '''

        zf = SharedZipFileReader(BytesIO(assets_data))

        try:
            manifest = zf.read('manifest.json')
            manifest = json.loads(manifest)
        except Exception as e:
            raise Exception("Failed to read asset data: %s" % (str(e)))

        # Restore endpoints
        for info in manifest['endpoints']:
            # see add_static()
            # TODO: Make common method for add_static() and load_assets_module to call
            url = info['url']
            file = SavedAssetFile(
                zf = zf,
                zf_name = info['filename'],
                metadata = info['asset'])
            self.__endpoints[url] = StaticEndpoint(asset = file)

        # Restore assets
        for info in manifest['assets']:
            # see add_asset()
            # TODO: Make common method for add_asset() and load_assets_module to call
            name = info['name']
            file = SavedAssetFile(
                zf = zf,
                zf_name = info['filename'],
                metadata=info['asset'])
            self.__assets[name] = file


