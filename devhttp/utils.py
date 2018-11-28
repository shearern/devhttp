import os
from threading import RLock

from zipfile import ZipFile, ZIP_STORED

def find(root):
    for filename in os.listdir(root):
        path = os.path.join(root, filename)
        if os.path.isfile(path):
            yield filename
        elif os.path.isdir(path):
            for sub_path in find(path):
                yield os.path.join(filename, sub_path)


def normalize_url(url):
    return url.replace("\\", '/').strip('/')


class SharedZipFileReader(ZipFile):

    def __init__(self, file, compression=ZIP_STORED, allowZip64=True):
        self.__lock = RLock()
        mode = "r"
        super().__init__(file, mode, compression, allowZip64)

    def read(self, name, pwd=None):
        with self.__lock:
            return super().read(name, pwd)

    def getinfo(self, name):
        with self.__lock:
            return super().getinfo(name)

    def infolist(self):
        with self.__lock:
            return super().infolist()







