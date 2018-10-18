


class StaticFile:
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
