import timeit

from zmlx.alg.fsys import samefile
from zmlx.alg.base import time2str
from zmlx.ui.alg import add_code_history
from zmlx.ui.break_point import BreakPoint
from zmlx.ui.cfg import *
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtWidgets
from zmlx.ui.shared_value import SharedValue
from zmlx.ui.widget.code_edit import CodeEdit
from zmlx.ui.widget.console_output import ConsoleOutput
from zmlx.ui.widget.console_thread import ConsoleThread


class ConsoleWidget(QtWidgets.QWidget):
    sig_kernel_started = QtCore.pyqtSignal()
    sig_kernel_done = QtCore.pyqtSignal()
    sig_kernel_err = QtCore.pyqtSignal(str)
    sig_refresh = QtCore.pyqtSignal()

    def __init__(self, parent, pre_task=None, post_task=None):
        super(ConsoleWidget, self).__init__(parent)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QtWidgets.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        main_layout.addWidget(self.splitter)

        self.output_widget = ConsoleOutput(self.splitter, console=self)
        self.input_editor = CodeEdit(self.splitter)

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addItem(QtWidgets.QSpacerItem(40, 20,
                                               QtWidgets.QSizePolicy.Policy.Expanding,
                                               QtWidgets.QSizePolicy.Policy.Minimum))

        def add_button(text, icon, slot):
            button = QtWidgets.QPushButton(self)
            button.setText(get_text(text))
            button.setIcon(load_icon(icon))
            button.clicked.connect(slot)
            h_layout.addWidget(button)
            return button

        self.button_exec = add_button('运行', 'begin',
                                      lambda: self.exec_file(fname=None))
        self.button_exec.setToolTip(
            '运行此按钮上方输入框内的脚本. 如需要运行标签页的脚本，请点击工具栏的运行按钮')
        self.button_exec.setShortcut('Ctrl+Return')
        self.button_pause = add_button('暂停', 'pause', self.pause_clicked)
        self.button_exit = add_button('终止', 'stop', self.stop_clicked)
        self.button_exit.setToolTip(
            '安全地终止内核的执行 (需要提前在脚本内设置break_point)')
        h_layout.addItem(QtWidgets.QSpacerItem(40, 20,
                                               QtWidgets.QSizePolicy.Policy.Expanding,
                                               QtWidgets.QSizePolicy.Policy.Minimum))
        main_layout.addLayout(h_layout)

        self.kernel_err = None
        self.thread = None
        self.result = None
        try:
            self.workspace = app_data.get()
            self.workspace.update({'__name__': '__main__', 'gui': gui})
        except Exception as err:
            print(err)
            self.workspace = {'__name__': '__main__', 'gui': gui}

        self.text_when_beg = None
        self.text_when_end = None
        self.time_beg = None
        self.time_end = None

        self.restore_code()

        self.break_point = BreakPoint(self)
        self.flag_exit = SharedValue(False)
        self.pre_task = pre_task
        self.post_task = post_task

    def refresh_buttons(self):
        if self.should_pause():
            self.button_pause.setText(get_text('继续'))
            self.button_pause.setIcon(load_icon('begin'))
            self.button_pause.setStyleSheet('background-color: #e15631; ')
        else:
            self.button_pause.setText(get_text('暂停'))
            self.button_pause.setIcon(load_icon('pause'))
            self.button_pause.setStyleSheet('')
        if self.flag_exit.value:
            self.button_exit.setStyleSheet('background-color: #e15631; ')
        else:
            self.button_exit.setStyleSheet('')
        if self.thread is None:
            self.button_exec.setStyleSheet('')
            self.button_exec.setEnabled(True)
            self.button_pause.setEnabled(False)
            self.button_exit.setEnabled(False)
            self.input_editor.setVisible(True)
        else:
            self.button_exec.setStyleSheet('background-color: #e15631; ')
            self.button_exec.setEnabled(False)
            self.button_pause.setEnabled(True)
            self.button_exit.setEnabled(True)
            self.input_editor.setVisible(
                samefile(self.workspace.get('__file__'),
                         self.input_editor.get_fname()))

    def pause_clicked(self):
        app_data.log(f'execute <pause_clicked> of {self}')
        self.set_should_pause(not self.should_pause())

    def should_pause(self):
        return self.break_point.locked()

    def set_should_pause(self, value):
        if value != self.should_pause():
            if self.break_point.locked():
                self.break_point.unlock()
            else:
                self.break_point.lock()
            self.sig_refresh.emit()

    def stop_clicked(self):
        app_data.log(f'execute <stop_clicked> of {self}')
        self.set_should_stop(not self.flag_exit.value)

    def set_should_stop(self, value):
        self.flag_exit.value = value
        if value:
            self.set_should_pause(False)
        self.sig_refresh.emit()

    def exec_file(self, fname=None):
        if fname is None:
            fname = self.input_editor.get_fname()
            self.input_editor.save()
            if fname is None:
                return
        if os.path.isfile(fname):
            add_code_history(fname)
            try:
                rel = os.path.relpath(fname)  # 当工作路径和fname不再同一个磁盘的时候，会触发异常
                self.text_when_beg = f"Start: {fname if len(fname) < len(rel) * 2 else rel}"
            except:
                self.text_when_beg = f"Start: {fname}"
            self.text_when_end = 'Done'
            self.workspace['__file__'] = fname
            app_data.log(f'execute file: {fname}')  # since 230923
            self.start_func(lambda:
                            exec(read_text(fname, encoding='utf-8', default=''),
                                 self.workspace))

    def start_func(self, code):
        if self.thread is not None:
            play_error()
            return
        self.result = None
        if isinstance(code, str):
            self.thread = ConsoleThread(lambda: exec(code, self.workspace))
        else:
            self.thread = ConsoleThread(code)
        self.thread.sig_done.connect(self.__kernel_exited)
        self.thread.sig_err.connect(self.__kernel_err)
        if self.pre_task is not None:
            self.pre_task()
        priority = load_priority()
        if self.text_when_beg is not None:
            print(f'{self.text_when_beg} ({priority})')
        self.time_beg = timeit.default_timer()
        self.set_should_stop(False)
        self.set_should_pause(False)
        self.thread.start(priority_value(priority))
        self.sig_kernel_started.emit()
        self.sig_refresh.emit()

    def __kernel_exited(self):
        if self.thread is not None:
            self.result = self.thread.result
            self.thread.result = None
            self.thread = None
            self.set_should_stop(False)
            self.set_should_pause(False)

            if self.text_when_end is not None:
                print(self.text_when_end)

            self.time_end = timeit.default_timer()
            if self.time_beg is not None and self.time_end is not None:
                print(
                    f'Time used = {time2str(self.time_end - self.time_beg)}\n')

            self.text_when_beg = None
            self.text_when_end = None
            if self.post_task is not None:
                self.post_task()
            self.sig_kernel_done.emit()
            self.sig_refresh.emit()

    def __kernel_err(self, err):
        self.kernel_err = err
        print(f'Error: {err}')
        self.sig_kernel_err.emit(err)
        try:
            app_data.log(f'meet exception: {err}')
        except:
            pass

    def kill_thread(self):
        """
        杀死线程；一种非常不安全的一种终止方法
        """
        if self.thread is not None:
            reply = QtWidgets.QMessageBox.question(self, '杀死进程',
                                                   "强制结束当前进程，可能会产生不可预期的影响，是否继续?",
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                if self.thread is not None:
                    thread = self.thread
                    thread.sig_done.emit()
                    thread.terminate()

    def writeline(self, text):
        self.output_widget.write(f'{text}\n')

    def restore_code(self):
        try:
            self.input_editor.open(
                os.path.join(os.getcwd(), 'code_in_editor.py'))
        except:
            pass

    def get_fname(self):
        return self.input_editor.get_fname()

    def is_running(self):
        return self.thread is not None

    def get_break_point(self):
        return self.break_point

    def get_flag_exit(self):
        return self.flag_exit
