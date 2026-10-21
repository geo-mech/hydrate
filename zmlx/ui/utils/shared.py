"""跨线程共享容器（``SharedValue`` / ``SharedList`` / ``SharedDict``）.

这三个都是「一把 ``QMutex`` 守住一个原生容器」的最小封装，供 GUI 线程与内核
线程之间交换数据用。之所以要有它们，是因为直接共享一个 ``list`` / ``dict`` 在
多线程下没有任何原子性保证；而用 ``QMutex`` 而不是 ``threading.Lock``，是为了与
本目录其余代码（``GuiApi`` / ``TaskProc``）走同一套 Qt 原语。

⚠️ **本模块只依赖 ``QtCore``**（不用 ``QtWidgets``）：它会被 ``GuiApi`` 等模块
在导入期引用，保持依赖最小可以避免拉起整个控件层。

⚠️ 文件名**刻意叫 ``shared`` 而不是 ``threading``**：本模块放在 ``zmlx/ui/utils/``
下，一个叫 ``threading.py`` 的子模块虽然因「绝对导入」并不会真的遮蔽标准库
（Python 3 下 ``import threading`` 仍解析到标准库，已实测），但读代码的人一定会
先怀疑它遮蔽了 —— 换个名字就没有这个歧义。

Modified by DeepSeek, 2026-10-16: 从 ``zmlx/ui/utils.py`` 拆出（原样搬迁，未改行为）.
"""

from zmlx.ui.pyqt import QtCore


class SharedValue:
    """线程安全的值容器（基于 QMutex）。"""

    def __init__(self, value=None):
        self.__val = value
        self.__mtx = QtCore.QMutex()

    def get(self):
        self.__mtx.lock()
        buf = self.__val
        self.__mtx.unlock()
        return buf

    def set(self, new_value):
        self.__mtx.lock()
        self.__val = new_value
        self.__mtx.unlock()

    @property
    def value(self):
        return self.get()

    @value.setter
    def value(self, new_value):
        self.set(new_value)


class SharedList:
    """线程安全的列表（基于 QMutex）。"""

    def __init__(self, value=None):
        self.value = value if isinstance(value, list) else []
        self.mtx = QtCore.QMutex()

    def get(self, idx):
        self.mtx.lock()
        res = self.value[idx]
        self.mtx.unlock()
        return res

    def set(self, idx, value):
        self.mtx.lock()
        self.value[idx] = value
        self.mtx.unlock()

    def append(self, value):
        self.mtx.lock()
        self.value.append(value)
        self.mtx.unlock()

    def length(self):
        self.mtx.lock()
        res = len(self.value)
        self.mtx.unlock()
        return res


class SharedDict:
    """线程安全的字典（基于 QMutex）。"""

    def __init__(self, value=None):
        self.value = value if isinstance(value, dict) else {}
        self.mtx = QtCore.QMutex()

    def get(self, key, default=None):
        self.mtx.lock()
        res = self.value.get(key, default)
        self.mtx.unlock()
        return res

    def set(self, key, value):
        self.mtx.lock()
        if value is None:
            self.value.pop(key, None)
        else:
            self.value[key] = value
        self.mtx.unlock()

    def list_keys(self, sort=True):
        self.mtx.lock()
        keys = list(self.value.keys())
        self.mtx.unlock()
        if sort:
            keys.sort()
        return keys
