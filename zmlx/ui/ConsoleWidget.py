# -*- coding: utf-8 -*-


from zml import gui, time_string, time2str
from zmlx.ui.BreakPoint import BreakPoint
from zmlx.ui.CodeEdit import CodeEdit
from zmlx.ui.Config import *
from zmlx.ui.ConsoleOutput import ConsoleOutput
from zmlx.ui.ConsoleThread import ConsoleThread
from zmlx.ui.GuiItems import *
from zmlx.ui.SharedValue import SharedValue
import shutil
import timeit


class ConsoleWidget(QtWidgets.QWidget):
    sig_kernel_started = QtCore.pyqtSignal()
    sig_kernel_done = QtCore.pyqtSignal()
    sig_kernel_err = QtCore.pyqtSignal(str)
    sig_cwd_changed = QtCore.pyqtSignal(str)

    def __init__(self, parent, pre_task=None, post_task=None):
        super(ConsoleWidget, self).__init__(parent)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QtWidgets.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        main_layout.addWidget(self.splitter)

        self.output_widget = ConsoleOutput(self.splitter)
        self.input_editor = CodeEdit(self.splitter)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addItem(h_spacer())

        def add_button(text, icon, slot):
            button = QtWidgets.QPushButton(self)
            button.setText(get_text(text))
            button.setIcon(load_icon(icon))
            button.clicked.connect(slot)
            h_layout.addWidget(button)
            return button

        self.button_exec = add_button('执行', 'begin.png',
                                      lambda: self.exec_file(fname=None))
        self.button_pause = add_button('暂停', 'pause.png', self.pause_clicked)
        self.button_exit = add_button('终止', 'stop.png', self.stop_clicked)
        h_layout.addItem(h_spacer())
        main_layout.addLayout(h_layout)

        self.kernel_err = None
        self.thread = None
        self.result = None
        try:
            self.workspace = data.get()
            self.workspace.update({'__name__': '__main__', 'gui': gui})
        except:
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

        self.sig_cwd_changed.connect(self.restore_code)

    def refresh_buttons(self):
        if self.should_pause():
            self.button_pause.setText(get_text('继续'))
            self.button_pause.setIcon(load_icon('begin.png'))
            self.button_pause.setStyleSheet('background-color: #e15631; ')
        else:
            self.button_pause.setText(get_text('暂停'))
            self.button_pause.setIcon(load_icon('pause.png'))
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

            def same_file(a, b):
                try:
                    return os.path.samefile(a, b)
                except:
                    return False

            self.input_editor.setVisible(same_file(self.workspace.get('__file__', None),
                                                   self.input_editor.get_fname()))

    def pause_clicked(self):
        data.log(f'execute <__button_pause_clicked> of {self}')
        self.set_should_pause(not self.should_pause())

    def should_pause(self):
        return self.break_point.locked()

    def set_should_pause(self, value):
        if value != self.should_pause():
            if self.break_point.locked():
                self.break_point.unlock()
            else:
                self.break_point.lock()
            self.refresh_buttons()

    def stop_clicked(self):
        data.log(f'execute <__button_exit_clicked> of {self}')
        self.set_should_stop(not self.flag_exit.value)

    def set_should_stop(self, value):
        self.flag_exit.value = value
        if value:
            self.set_should_pause(False)
        self.refresh_buttons()

    def exec_file(self, fname=None):
        if fname is None:
            fname = self.input_editor.get_fname()
            self.input_editor.save()
            if fname is None:
                return
        if os.path.isfile(fname):
            try:
                shutil.copy(fname, data.root('console_history', f'{time_string()}.py'))
            except:
                pass
            self.text_when_beg = f"{get_text('Start')}: {fname}"
            self.text_when_end = get_text('Done')
            self.workspace['__file__'] = fname
            self.start_func(lambda:
                            exec(read_text(fname, encoding='utf-8', default=''), self.workspace))

    def start_func(self, code):
        if self.thread is not None:
            play_error()
            # QtWidgets.QMessageBox.information(self, get_text('注意'), '内核正在运行，请等待当前任务执行结束')
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
        priority = load_console_priority()
        if self.text_when_beg is not None:
            print(f'{self.text_when_beg} ({get_priority_text(priority)})')
        self.time_beg = timeit.default_timer()
        self.set_should_stop(False)
        self.set_should_pause(False)
        self.thread.start(priority)
        self.sig_kernel_started.emit()
        self.refresh_buttons()

    def __kernel_exited(self):
        if self.thread is not None:
            self.result = self.thread.result
            self.thread.result = None
            self.thread = None
            self.set_should_stop(False)
            self.set_should_pause(False)

            if self.text_when_end is not None:
                print(f'{self.text_when_end}.')

            self.time_end = timeit.default_timer()
            if self.time_beg is not None and self.time_end is not None:
                print(f'Time used = {time2str(self.time_end-self.time_beg)}')

            self.text_when_beg = None
            self.text_when_end = None
            if self.post_task is not None:
                self.post_task()
            self.sig_kernel_done.emit()
            self.refresh_buttons()

    def __kernel_err(self, err):
        self.kernel_err = err
        self.sig_kernel_err.emit(err)
        QtWidgets.QMessageBox.information(self, 'Error', err)

    def kill_thread(self):
        """
        杀死线程；一种非常不安全的一种终止方法
        """
        if self.thread is not None:
            reply = QtWidgets.QMessageBox.question(self, '杀死进程',
                                                   "强制结束当前进程，可能会产生不可预期的影响，是否继续?",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                if self.thread is not None:
                    thread = self.thread
                    thread.sig_done.emit()
                    thread.terminate()

    def set_cwd_by_dialog(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, get_text('请选择工程文件夹'), os.getcwd())
        self.set_cwd(folder)

    def set_cwd(self, folder):
        if len(folder) > 0 and os.path.isdir(folder):
            try:
                os.chdir(folder)
                save_cwd()
                self.sig_cwd_changed.emit(os.path.abspath(os.getcwd()))
            except:
                pass

    def writeline(self, text):
        self.output_widget.write(f'{text}\n')

    def restore_code(self):
        try:
            self.input_editor.open(os.path.join(os.getcwd(), 'code_in_editor.py'))
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
