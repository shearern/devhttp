


class StaticFiles:
    '''Container listing static files that the server can serve'''

    def __init__(self):
        self.__files = dict()


    def has(self, name):
        return name in self.__files


    def add(self, static):
        if static.name in self.__files:
            raise KeyError("Assets %s already defined" % (static.name))
        self.__files[static.name] = static


    def get(self, name):
        return self.__files[name]