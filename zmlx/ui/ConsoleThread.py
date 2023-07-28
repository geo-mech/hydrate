from PyQt5 import QtCore


class ConsoleThread(QtCore.QThread):
    sig_done = QtCore.pyqtSignal()
    sig_err = QtCore.pyqtSignal(str)

    def __init__(self, code):
        super(ConsoleThread, self).__init__()
        self.code = code
        self.result = None

    def run(self):
        if self.code is not None:
            try:
                self.result = self.code()
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
            except BaseException as err:
                self.sig_err.emit(f'{err}')
        self.sig_done.emit()
