from PyQt5 import QtCore
from queue import Queue


class TaskProc(QtCore.QObject):
    __sig_do_task = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__tasks = Queue()
        self.__sig_do_task.connect(self.__do_task)

    def __do_task(self):
        while True:
            try:
                task = self.__tasks.get(block=False)
                if hasattr(task, '__call__'):
                    task()
            except:
                return

    def add(self, task):
        try:
            if hasattr(task, '__call__'):
                self.__tasks.put(task, block=False)
                self.__sig_do_task.emit()
        except:
            pass

