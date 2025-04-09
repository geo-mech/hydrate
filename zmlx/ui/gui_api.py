from zmlx.ui.cfg import get_text
from zmlx.ui.pyqt import QtCore, QtWidgets


class GuiApi(QtCore.QObject):
    sig_proc = QtCore.pyqtSignal(list)

    def __init__(self, parent, break_point=None, flag_exit=None):
        super(GuiApi, self).__init__(parent)
        self.sig_proc.connect(self.proc)
        self.break_point = break_point
        self.flag_exit = flag_exit
        self.funcs = {"add_func": self.add_func, "list_all": self.list_all}
        self.res = None
        self.err = None
        self.mtx = QtCore.QMutex()
        self.mtx_running = QtCore.QMutex()
        for key, val in self.get_standard(parent=parent).items():
            self.add_func(key, val)

    def add_func(self, key, func):
        self.funcs[key] = func
        return self

    def list_all(self):
        return self.funcs.keys()

    def proc(self, arg):
        assert len(arg) == 2
        args, kwargs = arg[0], arg[1]
        if len(args) > 0:
            try:
                f = self.funcs.get(args[0])
                assert f is not None, f'Function <{args[0]}> not found'
                self.res = f(*args[1:], **kwargs)
            except Exception as err:
                self.err = err
        self.mtx.unlock()

    def command(self, *args, **kwargs):
        has_bp = kwargs.pop('break_point', False)
        if has_bp:
            # 存在一个断点
            if self.break_point is not None:
                self.break_point.pass_only()
                if self.flag_exit is not None:
                    if self.flag_exit.value:
                        raise KeyboardInterrupt()
        if len(args) > 0:
            if self.mtx_running.tryLock():
                # 普通的函数，则通过信号槽的方式调用
                self.mtx.lock()
                self.res = None
                self.err = None
                self.sig_proc.emit([args, kwargs])
                self.mtx.lock()
                self.mtx.unlock()
                res = self.res
                err = self.err
                self.mtx_running.unlock()
                if err is not None:
                    raise err
                return res
            else:
                # 此刻，可能是函数调用函数的情况
                f = self.funcs.get(args[0])
                if f is not None:
                    return f(*args[1:], **kwargs)
                else:
                    return None
        else:
            return None

    @staticmethod
    def get_standard(parent):
        def get_open_file_name(*args, **kwargs):
            fpath, _ = QtWidgets.QFileDialog.getOpenFileName(parent,
                                                             *get_text(args),
                                                             **get_text(kwargs))
            return fpath

        def get_save_file_name(*args, **kwargs):
            fpath, _ = QtWidgets.QFileDialog.getSaveFileName(parent,
                                                             *get_text(args),
                                                             **get_text(kwargs))
            return fpath

        def information(*args, **kwargs):
            QtWidgets.QMessageBox.information(parent, *get_text(args),
                                              **get_text(kwargs))

        def about(*args, **kwargs):
            QtWidgets.QMessageBox.about(parent, *get_text(args),
                                        **get_text(kwargs))

        def warning(*args, **kwargs):
            QtWidgets.QMessageBox.warning(parent, *get_text(args),
                                          **get_text(kwargs))

        def get_existing_directory(*args, **kwargs):
            folder = QtWidgets.QFileDialog.getExistingDirectory(None,
                                                                *get_text(args),
                                                                **get_text(
                                                                    kwargs))
            return folder

        def question(info):
            reply = QtWidgets.QMessageBox.question(parent, get_text('请选择'),
                                                   get_text(info),
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return False
            else:
                return True

        return {'question': question, "information": information,
                "about": about, "warning": warning,
                'get_open_file_name': get_open_file_name,
                'get_save_file_name': get_save_file_name,
                'get_existing_directory': get_existing_directory,
                }
