from abc import ABC, abstractmethod

class Response(ABC):
    '''A response to an HTTP request'''

    @abstractmethod
    def content(self):
        '''Return content binary'''

    @abstractmethod
    def content_type(self):
        '''Return content type to return'''

    @abstractmethod
    def response_size(self):
        '''Return size of content binary'''


class StaticFileResponse(Response):

    def __init__(self, static_file):
        self.__file = static_file

    def response_size(self):
        return self.__file.size

    def content_type(self):
        '''Return content type to return'''
        return self.__file.content_type

    def content(self):
        with open(self.__file.path, 'rb') as fh:
            return fh.read()


class DynamicResponse(Response):

    def __init__(self, content, content_type):
        self.__content = content
        self.__content_type = content_type

        if self.__content.__class__ is str:
            self.__content = self.__content.encode('utf-8')


    def response_size(self):
        return len(self.__content)

    def content_type(self):
        '''Return content type to return'''
        return self.__content_type

    def content(self):
        return self.__content

