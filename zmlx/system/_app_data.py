"""应用数据存储（app_data 全局单例）。

⚠️⚠️ **这里有两套**互不相干**的存储，用错了一方会「写进去却读不到」**：

================  =====================  ==============  ==================
写入              读出                   存在哪           重启（新进程）后
================  =====================  ==============  ==================
``put`` / ``set`` ``get``                内存             **丢失**（读到 None）
``setenv``        ``getenv``             磁盘 ``env/``    **保留**
================  =====================  ==============  ==================

选哪个：

- **要跨进程保留**（下次启动还要用）-> ``setenv`` / ``getenv``
  ⚠️ 只能存 ``str``，列表 / 数字请自己 ``json.dumps``；
  ⚠️ 键名要足够独特（``getenv`` **先查系统环境变量**，通用名会被静默掩盖）。
- **只在本次运行内传递**（缓存、开关、会话对象）-> ``put`` / ``get``
  ⚠️ 能存任意 Python 对象，但重启即丢。

⚠️ 两套的**键名空间是独立的**：``put('x', 1)`` 之后 ``getenv('x')`` 读到的是
磁盘上那个文件，与内存里那份毫无关系。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-02: getenv() 改为**先查系统环境变量**、没有再回落到
持久化文件；新增 use_environ 开关（``path`` 键在 Windows 上会撞系统 PATH，故显式
关掉）。
Modified by DeepSeek, 2026-10-05: 补上「``put``/``get`` 与 ``setenv``/``getenv``
是两套存储」的说明。原先模块标题写的是「键值持久化」、而 ``put`` 的文档只说
「数据仅存在于运行时内存中」，两处都没点明**新进程读不到** —— 实测踩过：以为
``put`` 存的历史下次启动还能读到，实际是 ``None``。
"""
import datetime
import os
import shutil
import sys
import warnings
from pathlib import Path
from typing import Any, List, Optional, Union

from zmlx.system._fsys import make_parent
from zmlx.system._hash import get_hash
from zmlx.system._os import in_windows, in_macos
from zmlx.system._text import write_text, read_text


def get_user_data_dir(roaming: bool = False) -> str:
    """
    获取用户数据目录(支持roaming)
    """
    # Windows 系统
    if in_windows():
        # 优先使用 LOCALAPPDATA（不可漫游）或 APPDATA（可漫游）
        base_path_str = os.getenv(
            "LOCALAPPDATA" if not roaming else "APPDATA", "")
        if len(base_path_str) > 0 and os.path.exists(base_path_str):
            base_path = Path(base_path_str)
        else:  # 环境变量缺失时的后备方案
            base_path = Path.home() / "AppData" / (
                "Local" if not roaming else "Roaming")

    # macOS 系统
    elif in_macos():
        base_path = Path.home() / "Library" / "Application Support"

    # Linux/Unix 系统
    else:
        # 遵循 XDG Base Directory 规范
        xdg_data_home = os.getenv("XDG_DATA_HOME", "")
        if len(xdg_data_home) > 0:
            base_path = Path(xdg_data_home)
        else:
            base_path = Path.home() / ".local" / "share"

    # 创建并返回应用专属目录
    app_dir = base_path / 'zml'
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir)


class _AppData:
    """应用程序数据管理核心类，负责持久化存储和运行时数据管理。

    主要功能包括：
    - 跨平台缓存目录管理
    - 自定义文件搜索路径管理
    - 内存键值空间存储
    - 环境变量持久化存储
    - 日志记录和标签跟踪
    """

    def __init__(self):
        """
        初始化应用程序数据管理系统。
        """
        self.__folder = get_user_data_dir(roaming=True)

        # memory variable
        self.__space = {}

        # Custom file search path
        self.__custom_paths = []
        try:
            # ⚠️ use_environ=False：这里的 ``path`` 是**本软件自己的**搜索路径
            #    列表（env/path 文件，分号分隔），与系统的 ``PATH`` 无关；而
            #    Windows 查环境变量不区分大小写，不排除的话会读到整个 PATH。
            path_ = self.getenv(key='path', default='', use_environ=False)
            if isinstance(path_, str):
                for line in path_.split(';'):
                    line = line.strip()
                    if os.path.isdir(line):
                        self.add_path(line)
        except Exception as err:
            warnings.warn(f'Error: {err}', stacklevel=2)

    @property
    def folder(self) -> str:
        """
        获取应用程序缓存目录路径。
        """
        return self.__folder

    @property
    def space(self) -> dict:
        """
        获取应用程序缓存键值空间。
        """
        return self.__space

    def add_path(self, path: str) -> bool:
        """添加自定义文件搜索路径。

        Args:
            path (str): 要添加的目录路径

        Returns:
            bool: 成功添加返回True，路径无效或已存在返回False

        Note:
            - 使用 os.path.samefile 进行路径去重检查
            - 仅接受有效目录路径
        """
        if os.path.isdir(path):
            for existed in self.__custom_paths:
                if os.path.samefile(path, existed):
                    return False
            self.__custom_paths.append(path)
            return True
        else:
            return False

    def has_tag_today(self, tag: str) -> bool:
        """检查当天是否已标记特定标签。

        Args:
            tag (str): 标签标识符

        Returns:
            bool: 当天已有该标签返回True，否则返回False
        """
        name = get_hash(datetime.datetime.now().strftime(f"%Y-%m-%d.{tag}"))
        path = self.root('tags', name)
        return os.path.exists(path)

    def add_tag_today(self, tag: str):
        """为当天添加永久性时间戳标签。

        Args:
            tag (str): 标签标识符

        Note:
            - 静默处理所有IO异常
            - 标签文件存储在缓存目录的tags子目录
            - 文件内容为空，仅通过存在性标记
        """
        try:
            name = get_hash(datetime.datetime.now().strftime(f"%Y-%m-%d.{tag}"))
            path = self.root('tags', name)
            with open(path, 'w') as f:
                f.write('\n')
        except Exception:
            pass

    def log(self, text: str, encoding: Optional[str] = None):
        """记录运行时日志到日期命名的日志文件。

        Args:
            encoding: 编码格式，默认为utf-8
            text (str): 要记录的日志内容

        Note:
            - 日志文件存储在缓存目录的logs子目录
            - 每日日志存储在 YYYY-MM-DD.log 文件中
            - 自动创建所需目录结构
        """
        try:
            name = datetime.datetime.now().strftime("%Y-%m-%d.log")
            path = self.root('logs', name)
            if encoding is None:
                encoding = 'utf-8'
            with open(path, 'a', encoding=encoding) as f:
                f.write(f'{datetime.datetime.now()}: \n{text}\n\n\n')
        except Exception:
            pass

    def getenv(self, key: str, encoding: Optional[str] = None, default: Optional[Any] = None,
               ignore_empty: Optional[bool] = True,
               use_environ: bool = True) -> Optional[str]:
        """读取环境变量的值。

        查找顺序（**系统环境变量优先**）：

        1. **系统环境变量** ``os.environ[key]`` —— 便于从命令行 / CI / 容器
           临时覆盖某个设置，而不必去改磁盘上的持久化文件；
        2. **持久化文件**（缓存目录下的 ``env/<key>``，即 :meth:`setenv` 写入的
           那一份）—— 只有第 1 步没有取到值时才走这里。

        ``ignore_empty`` 对**两个来源同时生效**：空字符串视为「没有定义」，
        于是继续往下找；两处都没有时返回 ``default``。

        ⚠️⚠️ **本方法与 :meth:`get` 不是同一套存储，别混用**：

        ================  =====================  ==========================
        用哪一对           存在哪                  重启（新进程）后还在吗
        ================  =====================  ==========================
        ``set`` / ``put``  内存 ``self.space``      **不在**，读到 ``None``
        ``get``
        ``setenv``         磁盘文件 ``env/<key>``  **在**
        ``getenv``
        ================  =====================  ==========================

        所以**要跨进程保留**（下次启动还要用）的数据请用这一对；只在本次运行内
        传递的临时状态用 ``put`` / ``get``（那一对还能存任意对象，不必序列化）。

        ⚠️ 另外三点与 ``get`` 不同：

        - 本方法**只能取到字符串**（``os.environ`` 本身就是字符串，持久化文件也按
          文本读）。要存列表 / 数字，请自己用 ``json.dumps`` / ``json.loads`` 包一层；
          ⚠️ 写侧同样是字符串限定：``setenv`` 传非字符串会**直接抛 ``TypeError``**；
        - 本方法**会先看系统环境变量**（见上），所以键名**必须足够独特** —— 用
          ``emails``、``path`` 这类通用名会被外部环境变量静默掩盖
          （实测：``setenv('PATH', ...)`` 之后 ``getenv('PATH')`` 拿到的仍是系统
          ``PATH``，写进去的那份**读不到**）；
        - 空字符串默认被视为「没有定义」（``ignore_empty``），于是会继续往下找、
          最终返回 ``default``；要存「空」这个值本身请传 ``ignore_empty=False``。

        Args:
            key (str): 环境变量名称, 必须为标准的变量名
            encoding (str, optional): 读取**持久化文件**时的编码格式，默认
                utf-8（系统环境变量取出来已经是 ``str``，与本参数无关）
            default (Any, optional): 默认返回值
            ignore_empty (bool): 是否将空字符串视为默认值
            use_environ (bool): 是否**先查系统环境变量**。⚠️ 默认 True；只有
                在这个键会与系统变量**撞名**时才需要传 False（例如本模块内部
                的 ``path`` 键 —— Windows 的环境变量查询不区分大小写，它会撞上
                系统的 ``PATH``）

        Returns:
            Optional[str]: 成功读取返回字符串值，失败返回默认值
        """
        # 1) 系统环境变量优先：允许从外部（命令行 / CI / 容器）临时覆盖，
        #    而不必改动持久化文件。
        if use_environ:
            res = os.environ.get(key)
            if ignore_empty:
                if isinstance(res, str) and len(res) == 0:
                    res = None
            if res is not None:
                return res

        # 2) 回落到持久化文件
        path = self.root('env', key)
        if encoding is None:
            encoding = 'utf-8'
        res = read_text(path, encoding=encoding, default=default)
        if ignore_empty:
            if isinstance(res, str):
                if len(res) == 0:
                    return default
        return res

    def setenv(self, key: str, value: str, encoding: Optional[str] = None):
        """设置持久化环境变量值。

        Args:
            key (str): 环境变量名称
            value (str): 要存储的值
            encoding (str, optional): 文件编码格式，默认使用utf-8

        Note:
            - 变量存储在缓存目录的env子目录
            - 每个变量对应单独文件
            - ⚠️ 这里写入的只是**持久化文件**；:meth:`getenv` 会**优先**返回
              同名的系统环境变量，所以外部已经定义了同名变量时，本次写入不会
              立刻生效（这正是不去覆盖外部配置的用意）
            - ⚠️⚠️ **本方法与 :meth:`put` / :meth:`set` 不是同一套存储**：
              ``setenv`` 写**文件**（重启后还在），``put`` 写**内存**（重启即丢）。
              实测：``put('k', [...])`` 之后新进程 ``get('k')`` 得到 ``None``，
              而 ``setenv('k', json.dumps([...]))`` 的内容新进程能原样读回。
              **要跨进程保留的数据必须用这一对**
            - ⚠️ ``value`` **只能是字符串**（内部按文本写文件）；传列表 / 数字会
              直接抛 ``TypeError``（实测），要存它们请自己 ``json.dumps`` 序列化。
              这一点与 ``put`` 不同 —— ``put`` 能直接存任意 Python 对象
            - ⚠️ **键名要足够独特**：:meth:`getenv` 会先查系统环境变量，
              用 ``emails`` 之类通用名会被外部环境静默掩盖
        """
        path = self.root('env', key)
        if encoding is None:
            encoding = 'utf-8'
        write_text(path, value, encoding=encoding)

    def root(self, *args: str) -> str:
        """获取缓存目录下的指定路径。

        Args:
            *args (str): 路径组成部分

        Returns:
            str: 完整绝对路径

        Note:
            - 自动创建父目录
            - 支持链式调用：app_data.root('data', 'input.txt')
        """
        return make_parent(os.path.join(self.folder, *args))

    def temp(self, *args: str) -> str:
        """获取临时文件路径并确保父目录存在。

        Args:
            *args (str): 路径组成部分

        Returns:
            str: 完整绝对路径

        Note:
            - 文件存储在缓存目录的temp子目录
            - 适合存储临时中间数据
        """
        return self.root('temp', *args)

    @staticmethod
    def proj(*args: str) -> str:
        """访问项目相关文件路径。

        Args:
            *args (str): 路径组成部分

        Returns:
            str: 项目目录下的完整路径

        Note:
            - 无参数时返回项目根目录（.zml）
            - 自动创建父目录
        """
        if len(args) == 0:
            # return to the root directory of the project file
            return os.path.join(os.getcwd(), '.zml')
        else:
            return make_parent(os.path.join(os.getcwd(), '.zml', *args))

    def clear_temp(self, *args: str):
        """递归删除临时文件或目录。

        Args:
            *args (str): 要清理的相对路径

        Note:
            - 无参数时清空整个临时目录
            - 使用 shutil.rmtree 进行递归删除
            - 静默处理所有文件操作异常
        """
        folder = self.temp()
        if os.path.isdir(folder):
            if len(args) == 0:
                shutil.rmtree(folder)
                return
            path = os.path.join(folder, *args)
            if os.path.isdir(path):
                shutil.rmtree(path)
                return
            if os.path.isfile(path):
                os.remove(path)

    def get_paths(self, first: Optional[str] = None) -> List[str]:
        """获取当前有效搜索路径列表。

        Args:
            first (str, optional): 优先搜索路径

        Returns:
            List[str]: 按优先级排序的搜索路径列表

        Note:
            默认搜索顺序：
            1. 指定优先路径（如有）
            2. 当前工作目录
            3. 项目目录
            4. 缓存目录
            5. 临时目录
            6. 自定义路径
            7. Python系统路径
        """
        paths = []
        if first is not None:
            paths.append(first)
        paths.extend([os.getcwd(), self.proj(), self.root(), self.temp()])
        return paths + self.__custom_paths + sys.path

    def find(self, *name: str, first: Optional[str] = None) -> Optional[str]:
        """查找指定文件的首个有效路径。

        Args:
            *name (str): 文件名或路径组成部分
            first (str, optional): 优先搜索路径

        Returns:
            Optional[str]: 找到返回绝对路径，否则返回None

        Note:
            - 支持多级目录查找：find('data', 'input.txt')
            - 静默处理无效路径异常
        """
        if len(name) > 0:
            for folder in self.get_paths(first):
                try:
                    path = os.path.join(folder, *name)
                    if os.path.exists(path):
                        return path
                except Exception as err:
                    warnings.warn(f'Meet Error: {err}')
        return None

    def find_all(self, *name: str, first: Optional[str] = None) -> List[str]:
        """查找指定文件的所有有效路径。

        Args:
            *name (str): 文件名或路径组成部分
            first (str, optional): 优先搜索路径

        Returns:
            List[str]: 去重后的绝对路径列表（保留发现顺序）

        Note:
            - 使用 os.path.samefile 进行路径去重
            - 返回列表包含所有有效匹配项
        """
        results = []
        if len(name) > 0:
            for folder in self.get_paths(first):
                try:
                    path = os.path.join(folder, *name)
                    if os.path.exists(path):
                        exists = False
                        for x in results:
                            if os.path.samefile(x, path):
                                exists = True
                                break
                        if not exists:
                            results.append(path)
                except Exception:
                    pass
        return results

    def get(self, *args: Union[str, int], **kwargs) -> Any:
        """从**内存空间**中读取数据（:meth:`put` / :meth:`set` 写的那一份）。

        Args:
            *args: 兼容字典的键查询参数
            **kwargs: 兼容字典的默认值参数

        Returns:
            Any: 键对应的值或默认值

        Note:
            无参数调用时返回整个内存空间字典

        ⚠️⚠️ **本方法与 :meth:`getenv` 不是同一套存储，别混用**：

        ================  =====================  ==========================
        用哪一对           存在哪                  重启（新进程）后还在吗
        ================  =====================  ==========================
        ``set`` / ``put``  内存 ``self.space``      **不在**，读到 ``None``
        ``get``
        ``setenv``         磁盘文件 ``env/<key>``  **在**
        ``getenv``
        ================  =====================  ==========================

        ⚠️ **要跨进程保留的数据必须用 :meth:`setenv`**：丢给 ``put`` 的键在
        **下一次启动**的程序里恒为默认值 —— 实测验证过（写进去的值在新进程里读出来
        是 ``None``，而 ``setenv`` 写的能原样读回）。

        反过来，只在本进程内传递的临时状态（缓存、开关、当前会话的对象）用这一对
        更合适：它能存**任意 Python 对象**，不必像 ``setenv`` 那样先序列化成字符串。
        """
        if len(args) == 0 and len(kwargs) == 0:
            return self.space
        else:
            return self.space.get(*args, **kwargs)

    def set(self, key: Union[str, int], value: Any):
        """存储数据到**内存空间**（:meth:`put` 的别名，两者**完全等价**）。

        与 :meth:`put` 是同一个实现（都写 ``self.space[key]``），保留两个名字只是
        为了兼容既有的两种写法。**不要**以为它们有「临时 / 持久」之分 —— 没有。

        Args:
            key (str | int): 数据标识符
            value (Any): 要存储的值

        Note:
            - 支持任意Python对象存储
            - 数据仅存在于运行时内存中
            - ⚠️⚠️ **不持久化**：重启（新进程）后读不到，:meth:`get` 会返回默认值。
              要跨进程保留请用 :meth:`setenv`（但它只能存 ``str``）
            - ⚠️ 与 :meth:`setenv` 是**两套独立存储**，同一个键名互不相干
        """
        self.space[key] = value

    def put(self, key: Union[str, int], value: Any):
        """存储数据到**内存空间**（:meth:`set` 的别名，两者**完全等价**）。

        Args:
            key (str | int): 数据标识符
            value (Any): 要存储的值

        Note:
            - 支持任意Python对象存储
            - 数据仅存在于运行时内存中
            - ⚠️⚠️ **不持久化**：重启（新进程）后读不到，:meth:`get` 会返回默认值。
              实测：本进程 ``put('k', [...])`` 之后，新进程 ``get('k')`` 得到
              ``None``；而 ``setenv('k', json.dumps([...]))`` 写的内容新进程能
              原样读回。**要跨进程保留的数据必须用 :meth:`setenv`**
            - ⚠️ 与 :meth:`setenv` 是**两套独立存储**，同一个键名互不相干
              （``put('x', 1)`` 之后 ``getenv('x')`` 读的是磁盘上那个文件）
        """
        self.space[key] = value


# 应用数据管理器实例
app_data = _AppData()
