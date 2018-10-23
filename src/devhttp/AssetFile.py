import os
import logging
from mimetypes import guess_type

from io import BytesIO
from zipfile import ZipFile

class AssetFile:
    '''A single static file that the server can serve'''

    STATIC_FILE = 'static'
    ASSET = 'asset'

    def __init__(self, asset_type, name, content_type, path, size):
        '''
        :param asset_type: The type of asset (can it be served directly)
        :param path: name or path of URL
        :param content_type: The content type to provide
        :param path: Path to the file on disk
        :param size: Size of the content in bytes
        '''

        self.__type = asset_type
        if self.__type not in (self.STATIC_FILE, self.ASSET):
            raise ValueError("Invalid asset type")

        self.__name = name
        self.__content_type = content_type
        self.__path = path
        self.__size = size

        self._load_file_attributes()


    def _load_file_attributes(self):
        '''Retrieve any additional attributes needed from disk'''

       # Make sure file exists
        if not os.path.exists(self.__path):
            raise NameError("File doesn't exist: %s" % (self.__path))

        # Guess content type from filename
        if self.__content_type is None:
            content_type = guess_type(self.__path)
            if content_type[0] is None:
                logging.getLogger(__name__).warning(
                    "Can't determine mimetype for %s" % (self.__path))
                self.__content_type = None
            else:
                self.__content_type = content_type[0]

        # Get file size
        if self.__size is None:
            self.__size = os.path.getsize(self.__path)


    @property
    def asset_type(self):
        return self.__type

    @property
    def name(self):
        return self.__name

    @property
    def content_type(self):
        return self.__content_type

    @property
    def path(self):
        return self.__path

    @property
    def size(self):
        return self.__size

    @property
    def content(self):
        with open(self.path, 'rb') as fh:
            return fh.read()


    def save_metadata(self):
        '''Return representation for SavedAssetFile'''
        return {
            'name':   self.name,
            'type':   self.asset_type,
            'ctype':  self.content_type,
            'size':   self.size,
        }


class SavedAssetFile(AssetFile):
    '''
    Asset file that was saved by DevelopmentHttpServer.save_assets_module()

    Contents will be read back from in-memory zip file
    '''

    def __init__(self, zf_data, zf_name, metadata):
        '''
        :param zf_data:
            Bytes contents of zipfile with asset contents

            Note: ZipFile and BytesIO declared in here to allow multiple
            assets to read the same in-memory bytes.

        :param zf_name:
            Name of the item in the ZipFile for this asset contents
            Note: I'm assuming it's ok to have multiple ZipFile objects
            using the same BytesIO
        :param metadata:
            Metadata saved by AssetFile.save_metadata()
        '''
        super().__init__(
            name = metadata['name'],
            asset_type = metadata['type'],
            content_type = metadata['ctype'],
            path = None,
            size = metadata['size'])

        self.__zf = ZipFile(BytesIO(zf_data))
        self.__zf_name = zf_name


    def _load_file_attributes(self):
        '''Retrieve any additional attributes needed from disk'''
        pass

    @property
    def content(self):
        return self.__zf.read(self.__zf_name)

