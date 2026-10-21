"""文件处理分发（``FileHandler`` / ``CodeFile``）.

``FileHandler`` 维护「描述 → (扩展名, 打开函数, 新建函数)」的注册表，供主窗口的
「文件 → 打开 / 新建」菜单按扩展名选派处理函数；扩展名撞车时弹一个选择框让用户
挑。``CodeFile`` 是「一个可以读出源码的路径」的薄包装（控制台拿它当脚本执行）。

⚠️ ``FileHandler.open_file`` 在目标是目录时会让 GUI **切换工作目录**（走
``gui.set_cwd``），而不是「打开目录」—— 这是刻意的：用户在打开对话框里选中一个
目录，意图通常是「切到那儿去」。

⚠️ 2026-11-02 起另有 :meth:`FileHandler.open_files`（**批量**，拖放用）：多类型选择框
按扩展名缓存（每类只问一次）、未知类型**不弹窗**而把清单交回调用方。两者共用私有
:meth:`FileHandler._resolve`，所以「哪种扩展名归谁」只有一份实现。

Modified by DeepSeek, 2026-10-16: 从 ``zmlx/ui/utils.py`` 拆出（原样搬迁，未改行为）.
Modified by DeepSeek, 2026-11-02: 抽出 ``_resolve``，新增 ``open_files``（拖放批量打开）.
"""

import os

from zmlx.algs.sys import unique
from zmlx.system import read_text
from zmlx.ui.alg import modify_file_exts
from zmlx.ui.pyqt import QtCore, QtWidgets


class CodeFile:
    """代码文件包装器（支持文本读取与存在性检查）。"""

    def __init__(self, fname):
        self.fname = fname

    def __str__(self):
        return f"CodeFile({self.fname})"

    def __repr__(self):
        return str(self)

    def abs_path(self):
        if isinstance(self.fname, str):
            return os.path.abspath(self.fname)
        else:
            return ''

    def get_text(self):
        return read_text(
            self.abs_path(), encoding='utf-8', default='')

    def exists(self):
        return os.path.isfile(self.abs_path())


class FileHandler(QtCore.QObject):
    """
    管理文件处理函数
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__handlers = {}  # key = desc, value = [exts, open, new_file]
        self.parent = parent

    def add(self, desc, exts, open_file=None, new_file=None):
        """
        添加文件类型
        """
        if not isinstance(exts, (list, tuple)):
            if not isinstance(exts, str):
                raise TypeError(f'exts must be str or list, got {type(exts).__name__}')
            exts = [exts]

        exts = modify_file_exts(exts)

        value = self.__handlers.get(desc, None)

        if value is None:
            self.__handlers[desc] = [exts, open_file, new_file]
        else:  # 对于同样的描述，只能适用于某一个函数
            self.__handlers[desc] = [unique(value[0] + exts), open_file, new_file]

    def get(self, desc):
        """
        根据文件类型描述找文件处理函数
        """
        value = self.__handlers.get(desc, None)
        if value is None:
            return [desc, None, None, None]
        else:
            return [desc, value[0], value[1], value[2]]

    def find(self, ext):
        """
        根据文件扩展名找处理函数
        """
        ext = ext.lower()
        if len(ext) > 0:
            if ext[0] != '.':
                ext = '.' + ext
        results = []
        for desc, value in self.__handlers.items():
            if ext in value[0]:
                results.append([desc, value[0], value[1], value[2]])
        return results

    def _resolve(self, filepath, cache=None):
        """把一个路径解析成「该由哪个函数打开」（``open_file`` / ``open_files`` 共用）.

        Args:
            filepath: 文件或目录路径。
            cache: 可选字典（``扩展名 -> 处理函数``）。批量打开时传**同一个**字典，
                「同一个扩展名可能是多种类型」的选择框就只会弹一次。

        Returns:
            ``(func, reason)``，``reason`` 取下列之一：

            - ``'ok'`` —— ``func`` 可调用，用它打开；
            - ``'dir'`` —— 这是目录（本类不对目录做「打开」）；
            - ``'unknown'`` —— 扩展名没有注册处理器，或用户在类型选择框里取消了；
            - ``'missing'`` —— 路径不存在；
            - ``'invalid'`` —— 不是字符串。
        """
        if not isinstance(filepath, str):
            return None, 'invalid'

        if not os.path.isfile(filepath):
            return (None, 'dir') if os.path.isdir(filepath) else (None, 'missing')

        ext = os.path.splitext(filepath)[-1].lower()

        if cache is not None and ext in cache:
            func = cache[ext]
            return (func, 'ok') if callable(func) else (None, 'unknown')

        funcs = self.find(ext)

        if len(funcs) == 0:
            func = None
        elif len(funcs) == 1:
            func = funcs[0][2]
        else:
            items = [x[0] for x in funcs]
            desc, ok = QtWidgets.QInputDialog.getItem(
                self.parent, '此扩展名可能是多种文件类型', '请选择',
                items, editable=False)
            func = None
            if ok:
                for x in funcs:
                    if desc == x[0]:
                        func = x[2]
                        break

        if cache is not None:
            cache[ext] = func  # 取消也记下来 —— 否则拖入 5 个同类型文件要问 5 次

        return (func, 'ok') if callable(func) else (None, 'unknown')

    def open_file(self, filepath):
        """
        打开文件
        """
        func, reason = self._resolve(filepath)

        if reason == 'dir':
            from zmlx.ui.gui_buffer import gui
            gui.set_cwd(filepath)  # 浏览文件夹
            return None

        if reason in ('unknown', 'missing'):
            self.show_info(filepath)
            return None

        if reason != 'ok':
            return None

        try:
            return func(filepath)
        except Exception as err:
            print(f'Error: filepath = {filepath} \nmessage = {err}')
            return None

    def open_files(self, filepaths, *, set_cwd=True):
        """**批量**打开（拖放一次拖进多个文件时用），逐个异常隔离.

        Args:
            filepaths: 路径列表（也接受单个字符串）。
            set_cwd: 遇到目录时是否让 GUI 切换工作目录（与 :meth:`open_file`
                对目录的处理一致）。多个目录只切**最后一个**。

        Returns:
            dict: ``{'opened': [...], 'unknown': [...], 'dirs': [...], 'skipped': [...]}``
            —— ``opened`` 已成功打开；``unknown`` 扩展名没有注册处理器；``dirs`` 收到
            的目录；``skipped`` 打开了但抛异常。

        ⚠️ 与 :meth:`open_file` 的两点**刻意不同**：

        1. 未知扩展名**不弹** ``show_info``（一次拖进 10 个未知文件弹 10 个窗口没法用），
           改为把清单交回调用方，由它汇总成一条提示；
        2. 「多类型选择框」按扩展名缓存，**每类只问一次**。

        ⚠️ 打开动作本身是**同步**的：建标签页必须发生在 GUI 线程，所以别指望它
        在后台跑；调用方自己负责「慢」的反馈（主窗口拖放时设等待光标）。
        """
        if isinstance(filepaths, str):
            filepaths = [filepaths]

        cache = {}
        result = {'opened': [], 'unknown': [], 'dirs': [], 'skipped': []}
        folders = []

        for filepath in filepaths:
            func, reason = self._resolve(filepath, cache)

            if reason == 'ok':
                try:
                    func(filepath)
                    result['opened'].append(filepath)
                except Exception as err:
                    print(f'Error: filepath = {filepath} \nmessage = {err}')
                    result['skipped'].append(filepath)
            elif reason == 'dir':
                result['dirs'].append(filepath)
                folders.append(filepath)
            elif reason == 'unknown':
                result['unknown'].append(filepath)
            # 'missing' / 'invalid' 静默跳过：从邮件附件、压缩包条目拖出来的
            # 是「虚拟文件」，本来就没有本地路径，这是常态而不是错误。

        if set_cwd and len(folders) > 0:
            from zmlx.ui.gui_buffer import gui
            gui.set_cwd(folders[-1])

        return result

    @staticmethod
    def show_info(filepath):
        if os.path.isfile(filepath):
            from zmlx.algs.fsys import show_fileinfo
            show_fileinfo(filepath)

    def open_file_by_dlg(self, folder=None):
        """
        打开对话框，并基于选中的类型打开文件
        """
        if len(self.__handlers) == 0:
            return
        filter_text = '所有文件(*.*)'
        data = {}
        for desc, value in self.__handlers.items():
            exts, open_file, new_file = value
            if callable(open_file):
                desc += ' ('
                for ext in exts:
                    desc += f'*{ext}; '
                desc += ')'
                data[desc] = open_file
                filter_text += ';;'
                filter_text += desc
        if not isinstance(folder, str):
            folder = ''

        filepath, desc = QtWidgets.QFileDialog.getOpenFileName(
            self.parent, '请选择要打开的文件', folder, filter_text)

        if os.path.isfile(filepath):
            open_file = data.get(desc, None)
            if callable(open_file):
                open_file(filepath)
            else:  # 使用扩展名来查找
                self.open_file(filepath)

    def new_file_by_dlg(self, folder=None):
        """
        打开对话框，创建文件，并打开文件
        """
        if len(self.__handlers) == 0:
            print('没有设置任何的文件处理函数')
            return
        filter_text = None
        data = {}
        for desc, value in self.__handlers.items():
            exts, open_file, new_file = value
            if callable(new_file):
                desc += ' ('
                for i, ext in enumerate(exts):
                    if i + 1 == len(exts):
                        desc += f'*{ext}'
                    else:
                        desc += f'*{ext}; '
                desc += ')'
                data[desc] = [open_file, new_file]
                if filter_text is None:
                    filter_text = desc
                else:
                    filter_text += ';;'
                    filter_text += desc

        if len(data) == 0:
            print('没有用于新建文件的处理函数')
            return

        if not isinstance(folder, str):
            folder = ''

        filepath, desc = QtWidgets.QFileDialog.getSaveFileName(
            self.parent, '新建文件', folder, filter_text)

        print(f'filepath = {filepath}')
        print(f'desc = {desc}')

        value = data.get(desc, None)
        if value is None:
            print(f'对于给定类型，没有找到文件处理函数: {desc}')
            return

        assert isinstance(value, list)
        open_file = value[0]
        new_file = value[1]

        if callable(new_file):
            try:
                new_file(filepath)
                if callable(open_file):
                    open_file(filepath)
            except Exception as err:
                print(f'Error: filepath = {filepath} \nmessage = {err}')
                return
