from queue import Queue

from zmlx.ui.qt import QtCore


class TaskProc(QtCore.QObject):
    __sig_do_task = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__tasks = Queue()
        self.__sig_do_task.connect(self.__do_task)

    def _get_task(self):
        """
        弹出一个任务.
        """
        try:
            return self.__tasks.get(block=False)
        except:
            return None

    def __do_task(self):
        while True:
            try:
                task = self._get_task()
                if task is None:
                    break
                else:
                    assert callable(task), 'The task is not a function'
                    task()
            except Exception as e:
                print(f'meet error {e}')

    def add(self, task):
        try:
            if callable(task):
                self.__tasks.put(task, block=False)
                self.__sig_do_task.emit()
        except Exception as e:
            print(f'meet error {e}')
