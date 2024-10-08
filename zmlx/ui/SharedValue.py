from zmlx.ui.Qt import QtCore


class SharedValue:
    def __init__(self, value=None):
        self.__val = value
        self.__mtx = QtCore.QMutex()

    @property
    def value(self):
        self.__mtx.lock()
        buf = self.__val
        self.__mtx.unlock()
        return buf

    @value.setter
    def value(self, new_value):
        self.__mtx.lock()
        self.__val = new_value
        self.__mtx.unlock()
