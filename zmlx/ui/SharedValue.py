from PyQt5 import QtCore


class SharedValue:
    def __init__(self, value=None):
        self.__val = value
        self.__mtx = QtCore.QMutex()

    def get(self):
        self.__mtx.lock()
        value = self.__val
        self.__mtx.unlock()
        return value

    def set(self, value):
        self.__mtx.lock()
        self.__val = value
        self.__mtx.unlock()

    value = property(get, set)
