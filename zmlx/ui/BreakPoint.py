from PyQt5 import QtCore


class BreakPoint(QtCore.QObject):
    sig_unlocked = QtCore.pyqtSignal()
    sig_locked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(BreakPoint, self).__init__(parent)
        self.__mtx = QtCore.QMutex()
        self.__locked = False

    def pass_only(self):
        self.__mtx.lock()
        self.__mtx.unlock()

    def locked(self):
        return self.__locked

    def lock(self):
        if not self.__locked:
            self.__mtx.lock()
            self.__locked = True
            self.sig_locked.emit()

    def unlock(self):
        if self.__locked:
            self.__mtx.unlock()
            self.__locked = False
            self.sig_unlocked.emit()
