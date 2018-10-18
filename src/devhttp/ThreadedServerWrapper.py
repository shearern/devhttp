


class ThreadedServerWrapper:
    '''Wraps access to server attributes in a thread safe method'''

    def __init__(self, server):
        self.__server = server