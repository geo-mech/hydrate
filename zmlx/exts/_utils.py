"""
定义不依赖于DLL的通用的函数或者类
"""

import ctypes
import datetime
import hashlib
import os
import shutil
import sys
import warnings
from ctypes import c_void_p, c_double, POINTER
from pathlib import Path
from typing import Any, List
from typing import Optional, Callable
from typing import Union

try:
    import numpy as np
except ImportError:
    np = None

# 表征无穷大的序号值
IDX_INF: int = 2147483647


class Object:
    """
    提供受限属性管理的对象基类。
    """

    def set(self, **kwargs):
        """
        更新现有对象属性
        """
        current_keys = dir(self)
        for key, value in kwargs.items():
            assert key in current_keys, (f"add new attribution '{key}' "
                                         f"to {type(self).__name__} is forbidden")
            setattr(self, key, value)
        return self


def is_array(o: Any) -> bool:
    """判断对象是否支持类列表访问语义。

    Args:
        o (Any): 待检测对象

    Returns:
        bool: 当对象同时支持__getitem__和__len__协议时返回True
    """
    return hasattr(o, '__getitem__') and hasattr(o, '__len__')


def parse_fid3(fluid_id):
    """自动识别给定的流体 ID 为流体某个组分的 ID。

    Args:
        fluid_id: 流体 ID，可以是单个值或数组。

    Returns:
        tuple: 包含三个整数的元组，表示流体组件的 ID。如果未提供，则返回默认值 (IDX_INF, IDX_INF, IDX_INF)。
    """
    if fluid_id is None:
        return IDX_INF, IDX_INF, IDX_INF
    if is_array(fluid_id):
        count = len(fluid_id)
        assert 0 < count <= 3
        if count == 1:  # 此时，它仍然可能是一个array
            return parse_fid3(fluid_id[0])
        else:
            i0 = fluid_id[0] if 0 < count else IDX_INF
            i1 = fluid_id[1] if 1 < count else IDX_INF
            i2 = fluid_id[2] if 2 < count else IDX_INF
            return i0, i1, i2
    else:
        return fluid_id, IDX_INF, IDX_INF


def parse_fid(fluid_id):
    """自动识别给定的流体 ID 为流体某个组分的 ID。

    Args:
        fluid_id: 流体 ID，可以是单个值或数组。

    Returns:
        list: 流体ID序列
    """
    if fluid_id is None:
        return []
    if is_array(fluid_id):
        if len(fluid_id) == 1:  # 此时，它仍然可能是一个array
            return parse_fid(fluid_id[0])
        else:
            return fluid_id
    else:
        return [fluid_id]


def get_index(index: Optional[int], count: Optional[int] = None) -> Optional[int]:
    """返回修正后的序号，确保返回的序号满足 0 <= index < count。

    Args:
        index (Optional[int]): 原始序号。
        count (Optional[int]): 总数。默认为 None。

    Returns:
        Optional[int]: 修正后的序号。如果无法修正，则返回 None。
    """
    if index is None:
        return None
    if count is None:  # 此时，无法判断index是否越界
        if index >= 0:
            return index
        else:
            return None
    else:
        assert count >= 0
        if index >= 0:
            if index < count:
                return index  # 0 <= index < count
            else:
                return None
        else:
            assert index < 0
            index += count  # index < count
            if index >= 0:
                return index  # 0 <= index < count
            else:
                return None


def attr_in_range(value, *, left=None, right=None, min=None, max=None):
    """
    判断属性值是否在给定的范围内
    """
    if min is not None:
        warnings.warn(
            'The argument <min> of <_attr_in_range> '
            'will be removed after 2025-4-5, use <left> instead',
            DeprecationWarning, stacklevel=2)
        assert left is None
        left = min

    if max is not None:
        warnings.warn(
            'The argument <max> of <_attr_in_range> '
            'will be removed after 2025-4-5, use <right> instead',
            DeprecationWarning, stacklevel=2)
        assert right is None
        right = max

    if left is None:
        left = -1.0e100

    if right is None:
        right = 1.0e100

    return left <= value <= right


def get_distance(p0, p1):
    """计算两个点之间的距离。

    Args:
        p0: 第一个点的坐标。
        p1: 第二个点的坐标。

    Returns:
        float: 两个点之间的距离。
    """
    dist = 0.0
    for i in range(min(len(p0), len(p1))):
        dist += (p0[i] - p1[i]) ** 2
    return dist ** 0.5


def get_hash(text: str, length: Optional[int] = None) -> str:
    """
    计算文本的哈希值. 返回前length个字符.
    默认返回前30个字符.
    Args:
        text (str): 输入文本
        length (int, optional): 哈希值长度，默认为None
    Returns:
        str: 计算得到的哈希值
    """
    hash_obj = hashlib.sha256(text.encode('utf-8'))
    if length is None:
        length = 30
    return hash_obj.hexdigest()[:length]


def in_windows() -> bool:
    """
    判断当前是否处于Windows系统的运行环境
    Returns:
        bool: True表示是Windows系统，False表示不是
    """
    return sys.platform.startswith('win')


def in_linux() -> bool:
    """
    判断当前是否处于Linux系统的运行环境
    Returns:
        bool: True表示是Linux系统，False表示不是
    """
    return sys.platform.startswith('linux')


def in_macos() -> bool:
    """
    判断当前是否处于Mac系统
    Returns:
        bool: True表示是Mac系统，False表示不是
    """
    return sys.platform == 'darwin'


def get_os_type() -> str:
    """
    返回操作系统类型字符串 (注意，zml模块仅支持 Windows和Linux两个系统，在Mac系统未测试)
    """
    if in_windows():
        return 'windows'
    elif in_linux():
        return 'linux'
    elif in_macos():
        return 'macos'
    else:
        return 'unknown'


# 是否是Windows系统 (注: 此常量后续弃用，请使用函数 in_windows)
is_windows = in_windows()

# 是否是Linux系统 (注: 此常量后续弃用，请使用函数 in_linux)
is_linux = in_linux()

# 是否是MacOS系统 (注: 此常量后续弃用，请使用函数 in_macos)
is_macos = in_macos()


def make_dirs(folder: Optional[str] = None):
    """递归创建目录结构。

    Args:
        folder (str, optional): 要创建的目录路径

    Note:
        - 自动创建所有不存在的父目录
        - 使用exist_ok参数避免目录已存在的错误
        - 包含异常处理，失败时静默退出
    """
    try:
        if folder is not None:
            if not os.path.isdir(folder):
                os.makedirs(folder, exist_ok=True)
    except:
        pass


# Alias of the function < for compatibility with previous code >
makedirs = make_dirs


def make_parent(path: str) -> str:
    """确保指定文件路径的父目录存在。

    Args:
        path (str): 文件路径

    Returns:
        str: 原始输入路径

    Note:
        - 通过调用make_dirs实现目录创建
        - 始终返回输入路径以便链式调用
        - 包含异常处理机制保证程序健壮性
    """
    try:
        name = os.path.dirname(path)
        if not os.path.isdir(name):
            make_dirs(name)
        return path
    except:
        return path


def read_text(path: str, encoding: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
    """从文本文件中读取内容。

    Args:
        path (str): 目标文件路径
        encoding (str, optional): 文件编码格式，默认使用系统编码
        default (Any, optional): 读取失败时的默认返回值，默认为None

    Returns:
        Optional[str]: 成功时返回文件内容字符串，失败返回default值

    Note:
        - 自动处理文件不存在的情况
        - 静默处理所有I/O异常
        - 支持任意文本编码格式
    """
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        return default
    except:
        return default


def write_text(path: str, text: Optional[str] = None, encoding: Optional[str] = None):
    """将文本内容写入指定文件。

    Args:
        path (str): 目标文件路径
        text (str, optional): 要写入的文本内容，默认为None(写入空字符串)
        encoding (str, optional): 文件编码格式，默认使用系统编码

    Note:
        - 自动创建不存在的父目录
        - 静默处理所有I/O异常
        - 当text为None时写入空字符串
        - 使用原子写操作避免数据损坏
    """
    folder = os.path.dirname(path)
    if len(folder) > 0 and not os.path.isdir(folder):
        make_dirs(folder)
    with open(path, 'w', encoding=encoding) as f:
        if text is None:
            f.write('')
        else:
            f.write(text)


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


def check_ipath(path: str, obj=None):
    """在读取文件时检查输入的文件名。

    Args:
        path (str): 文件路径。
        obj: 读取文件的对象。

    Raises:
        AssertionError: 如果路径不是字符串或文件不存在。
    """
    assert isinstance(path, str), f'The given path <{path}> is not string while load {type(obj)}'
    assert os.path.isfile(path), f'The given path <{path}> is not file while load {type(obj)}'


class _AppData(Object):
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
            path_ = self.getenv(key='path', default='')
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
        except:
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
        except:
            pass

    def getenv(self, key: str, encoding: Optional[str] = None, default: Optional[Any] = None,
               ignore_empty: Optional[bool] = False) -> Optional[str]:
        """读取持久化环境变量值。

        Args:
            key (str): 环境变量名称, 必须为标准的变量名
            encoding (str, optional): 文件编码格式，默认使用utf-8
            default (Any, optional): 默认返回值
            ignore_empty (bool): 是否将空字符串视为默认值

        Returns:
            Optional[str]: 成功读取返回字符串值，失败返回默认值
        """
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
                except:
                    pass
        return results

    def get(self, *args: Union[str, int], **kwargs) -> Any:
        """从内存空间中读取数据。

        Args:
            *args: 兼容字典的键查询参数
            **kwargs: 兼容字典的默认值参数

        Returns:
            Any: 键对应的值或默认值

        Note:
            无参数调用时返回整个内存空间字典
        """
        if len(args) == 0 and len(kwargs) == 0:
            return self.space
        else:
            return self.space.get(*args, **kwargs)

    def put(self, key: Union[str, int], value: Any):
        """存储数据到内存空间。

        Args:
            key (str | int): 数据标识符
            value (Any): 要存储的值

        Note:
            - 支持任意Python对象存储
            - 数据仅存在于运行时内存中
        """
        self.space[key] = value


app_data = _AppData()


def log(text: str, tag: Optional[str] = None):
    """记录运行时日志信息。

    Args:
        text (str): 需要记录的日志内容
        tag (str, optional): 唯一标识标签，用于实现每日单次记录

    Returns:
        None

    Note:
        - 当指定 tag 时，确保当天只记录一次相同标签日志
        - 使用 app_data 的标签跟踪系统实现每日去重
        - 静默处理所有I/O异常
        - 实际日志存储路径由 _AppData 类管理
    """
    if tag is not None:
        if app_data.has_tag_today(tag):
            return
        else:
            app_data.add_tag_today(tag)
    app_data.log(text)


class HasHandle(Object):
    """管理具有句柄（handle）的对象的基类。

    该类提供了创建、释放和访问句柄的方法，用于管理具有句柄的对象。
    Args:
        handle: 对象的句柄。如果未提供，则会调用 `create` 方法创建一个新的句柄。
        create: 一个函数，用于创建新的句柄。
        release: 一个函数，用于释放句柄。
    """

    def __init__(self, handle: Optional[c_void_p] = None, create: Optional[Callable] = None,
                 release: Optional[Callable] = None):
        """初始化 HasHandle 对象。

        Args:
            handle: 对象的句柄。如果未提供，则会调用 `create` 方法创建一个新的句柄。
            create: 一个函数，用于创建新的句柄。
            release: 一个函数，用于释放句柄。
        """
        if handle is None:
            assert callable(create) and callable(release)
            self.__handle = create()
            self.__release = release
        else:
            assert handle, 'handle should be not None'
            self.__handle = handle
            self.__release = None

    def __del__(self):
        """在对象被销毁时调用，用于释放句柄。"""
        if callable(self.__release):
            self.__release(self.__handle)

    @property
    def handle(self) -> c_void_p:
        """获取对象的句柄。

        Returns:
            对象的句柄。
        """
        return self.__handle

    def __repr__(self) -> str:
        return f'{type(self).__name__}(handle={int(self.handle)})'

    def __str__(self) -> str:
        return repr(self)


def get_nearest_cell(model: Any, pos, mask=None):
    """
    找到model中，距离给定的pos最为接近的cell
    """
    if model.cell_number == 0:
        return None

    result = None
    dist = 1.0e100

    # 遍历，找到最接近的cell.
    for cell in model.cells:
        if mask is not None:
            if not mask(cell):  # 只有满足条件的cell才会被检查.
                continue

        # 计算距离
        d = get_distance(cell.pos, pos)
        if result is None or d < dist:
            dist = d
            result = cell  # 更新结果

    # 返回结果
    return result


def get_pos_range(model: Any, dim):
    """
    返回cells在某一个坐标维度上的范围

    参数:
    - model: 网格模型对象
    - dim: 维度索引（0表示x维度，1表示y维度，2表示z维度）

    返回:
    - l_range: 该维度上的最小位置值
    - r_range: 该维度上的最大位置值

    异常:
    - 断言错误: 如果模型中的单元格数量小于等于0，或者维度索引不在[0, 2]范围内
    """
    assert model.cell_number > 0
    assert 0 <= dim <= 2
    l_range, r_range = 1e100, -1e100
    for c in model.cells:
        p = c.pos[dim]
        l_range = min(l_range, p)
        r_range = max(r_range, p)
    return l_range, r_range


def get_cells_in_range(model: Any, xr=None, yr=None, zr=None,
                       center=None, radi=None):
    """
    返回在给定的坐标范围内的所有的cell. 其中xr为x坐标的范围，yr为y坐标的范围，zr为
    z坐标的范围。当某个范围为None的时候，则不检测.

    参数:
    - model: 网格模型对象
    - xr: x坐标范围（可选）
    - yr: y坐标范围（可选）
    - zr: z坐标范围（可选）
    - center: 中心点坐标（可选）
    - radi: 半径（可选）

    返回:
    - cells: 在给定范围内的单元格列表

    异常:
    - 无异常抛出
    """
    if xr is None and yr is None and zr is None and center is not None and radi is not None:
        cells = []
        for c in model.cells:
            if get_distance(center, c.pos) <= radi:
                cells.append(c)
        return cells
    ranges = (xr, yr, zr)
    cells = []
    for c in model.cells:
        out_of_range = False
        for i in range(len(ranges)):
            r = ranges[i]
            if r is not None:
                p = c.pos[i]
                if p < r[0] or p > r[1]:
                    out_of_range = True
                    break
        if not out_of_range:
            cells.append(c)
    return cells


def get_cell_mask(model: Any, xr=None, yr=None, zr=None):
    """
    返回给定坐标范围内的cell的index。主要用来辅助绘图。since 2024-6-12

    参数:
    - model: 网格模型对象
    - xr: x坐标范围（可选）
    - yr: y坐标范围（可选）
    - zr: z坐标范围（可选）

    返回:
    - mask: 在给定范围内的单元格索引列表

    异常:
    - 无异常抛出
    """

    def get_(v, r):
        """
        根据给定的值和范围生成一个布尔掩码。

        参数:
        - v: 值的列表
        - r: 范围（可选）

        返回:
        - mask: 布尔掩码列表
        """
        if r is None:
            return [True] * len(v)  # 此时为所有
        else:
            return [r[0] <= v[i] <= r[1] for i in range(len(v))]

    v_pos = [c.pos for c in model.cells]
    # 三个方向分别的mask
    x_mask = get_([pos[0] for pos in v_pos], xr)
    y_mask = get_([pos[1] for pos in v_pos], yr)
    z_mask = get_([pos[2] for pos in v_pos], zr)

    # 返回结果
    return [x_mask[i] and y_mask[i] and z_mask[i] for i in range(len(x_mask))]


def get_cell_pos(model: Any, index=(0, 1, 2)):
    """
    从网格模型中获取指定索引的单元格位置信息

    参数:
    - model: 网格模型对象
    - index: 索引元组，默认为 (0, 1, 2)，表示获取 x、y、z 坐标

    返回:
    - results: 包含指定索引位置信息的元组

    异常:
    - 无异常抛出
    """
    vpos = [cell.pos for cell in model.cells]
    results = []
    for i in index:
        results.append([pos[i] for pos in vpos])
    return tuple(results)


def get_cell_property(model: Any, get):
    """
    从网格模型中获取每个单元格的指定属性值

    参数:
    - model: 网格模型对象
    - get: 用于获取单元格属性的函数

    返回:
    - results: 包含每个单元格属性值的列表

    异常:
    - 无异常抛出
    """
    return [get(cell) for cell in model.cells]


def plot_tricontourf(model: Any, get, caption=None, gui_only=False, title=None,
                     triangulation=None,
                     fname=None, dpi=300):
    """
    绘制网格模型中每个单元格的指定属性值的三角剖分等值线图。

    参数:
    - model: 网格模型对象
    - get: 用于获取单元格属性的函数
    - caption: 图形标题（可选）
    - gui_only: 是否仅在图形用户界面中显示（可选）
    - title: 图形标题（可选）
    - triangulation: 三角剖分对象（可选）
    - fname: 保存文件名（可选）
    - dpi: 图像分辨率（可选）

    返回:
    - 无返回值

    异常:
    - 无异常抛出
    """
    from zmlx.plt.on_axes.data import tricontourf
    from zmlx.plt.on_figure import add_axes2, plot_on_figure
    from zmlx.ui import gui

    if gui_only and not gui.exists():
        return
    z = [get(cell) for cell in model.cells]
    if triangulation is None:
        pos = [cell.pos for cell in model.cells]
        x = [p[0] for p in pos]
        y = [p[1] for p in pos]
        o = tricontourf(x=x, y=y, z=z, triangulation=None, levels=20, cmap='coolwarm')
    else:
        o = tricontourf(z=z, triangulation=triangulation, levels=20, cmap='coolwarm')

    plot_on_figure(add_axes2, o, xlabel='x/m', ylabel='y/m', aspect='equal', title=title,
                   caption=caption, gui_only=gui_only, fname=fname, dpi=dpi)


class HasCells(Object):
    def get_pos_range(self, dim):
        return get_pos_range(self, dim)

    def get_cells_in_range(self, *args, **kwargs):
        return get_cells_in_range(self, *args, **kwargs)

    def get_cell_pos(self, *args, **kwargs):
        return get_cell_pos(self, *args, **kwargs)

    def get_cell_property(self, *args, **kwargs):
        return get_cell_property(self, *args, **kwargs)

    def plot_tricontourf(self, *args, **kwargs):
        plot_tricontourf(self, *args, **kwargs)


class Iterator:
    """迭代器类，用于遍历模型中的元素。

    Attributes:
        __model: 模型对象。
        __index: 当前迭代的索引。
        __count: 模型中元素的总数。
        __get: 获取元素的函数。

    Args:
        model: 要迭代的模型对象。
        count: 模型中元素的总数。
        get: 一个函数，用于获取模型中指定索引位置的元素。
    """

    def __init__(self, model: Any, count: int, get: Callable[[Any, int], Any]):
        """初始化迭代器对象。

        Args:
            model (Any): 要迭代的模型对象。
            count (int): 模型中元素的总数。
            get (Callable[[Any, int], Any]): 一个函数，用于获取模型中指定索引位置的元素。
        """
        self.__model = model
        self.__index = 0
        self.__count = count
        self.__get = get

    def __iter__(self) -> 'Iterator':
        """返回迭代器对象本身。

        Returns:
            Iterator: 迭代器对象本身。
        """
        self.__index = 0
        return self

    def __next__(self) -> Any:
        """返回下一个元素，如果没有更多元素则抛出 StopIteration 异常。

        Returns:
            下一个元素。

        Raises:
            StopIteration: 如果没有更多元素。
        """
        if self.__index < self.__count:
            cell = self.__get(self.__model, self.__index)
            self.__index += 1
            return cell
        else:
            raise StopIteration()

    def __len__(self) -> int:
        """返回模型中元素的总数。

        Returns:
            int: 模型中元素的总数。
        """
        return self.__count

    def __getitem__(self, ind: int) -> Any:
        """返回指定索引位置的元素。

        Args:
            ind (int): 索引位置。

        Returns:
            指定索引位置的元素。
        """
        if ind < self.__count:
            return self.__get(self.__model, ind)
        else:
            return None


def sendmail(address: str, subject: Optional[str] = None, text: Optional[str] = None,
             name_from: Optional[str] = None, name_to: Optional[str] = None) -> bool:
    """通过SMTP协议发送电子邮件。

    Args:
        address (str): 收件人邮箱地址
        subject (str, optional): 邮件主题，默认为发送者名称
        text (str, optional): 邮件正文内容，默认为空字符串
        name_from (str, optional): 发件人显示名称，默认获取系统用户名
        name_to (str, optional): 收件人显示名称，默认为'UserEmail'

    Returns:
        bool: 邮件发送成功返回True，失败返回False

    Note:
        - 使用固定SMTP服务器(smtp.126.com)和预配置账号
        - 邮件内容默认使用UTF-8编码
        - 包含异常处理机制，失败时静默返回False
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header
        if name_from is None:
            try:
                import getpass
                name_from = getpass.getuser()
            except:
                name_from = 'User'
        if name_to is None:
            name_to = 'UserEmail'
        if subject is None:
            subject = f'Message from {name_from}'
        if text is None:
            text = ''
        assert isinstance(text, str), f"text must be str, but got {type(text)}"
        message = MIMEText(text, 'plain', 'utf-8')
        message['From'] = Header(name_from)
        message['To'] = Header(name_to)
        message['Subject'] = Header(subject)
        smtp_obj = smtplib.SMTP()
        smtp_obj.connect("smtp.126.com", 25)
        smtp_obj.login("hyfrddm@126.com", "iggcas0617")
        smtp_obj.sendmail('hyfrddm@126.com',
                          [address], message.as_string())
        return True
    except:
        return False


def const_f64_ptr(arr):
    """
    对于给定的Array，返回一个POINTER(c_double)，指向它的内存地址.
    返回的这个地址主要用于“读取”
    Args:
        arr: 需要获得内存地址的Array

    Returns:
        POINTER(c_double) or None: 一个只读的指针.
    """
    if arr is None:
        return None

    if isinstance(arr, POINTER(c_double)):
        return arr

    if isinstance(arr, c_void_p):
        return ctypes.cast(arr, POINTER(c_double))

    if hasattr(arr, 'pointer'):
        return arr.pointer

    # 下面，处理numpy的数组
    if np is not None:
        arr = np.ascontiguousarray(arr, dtype=np.float64)
        return arr.ctypes.data_as(POINTER(c_double))
    else:
        raise ValueError(
            f"Can not convert to POINTER(c_double). type is {type(arr)}")


def f64_ptr(arr):
    """
    对于给定的Array，返回一个POINTER(c_double)，指向它的内存地址.
    返回的内容是可“读写”的
    Args:
        arr: 需要获得内存地址的Array

    Returns:
        POINTER(c_double) or None: 一个可供读写的内存地址
    """
    if arr is None:
        return None

    if isinstance(arr, POINTER(c_double)):
        return arr

    if isinstance(arr, c_void_p):
        return ctypes.cast(arr, POINTER(c_double))

    if hasattr(arr, 'pointer'):
        return arr.pointer

    # 下面，处理numpy的数组
    if np is not None:
        assert isinstance(arr, np.ndarray), "Input must be a NumPy array"
        assert arr.flags.c_contiguous, "Array must be C-contiguous"
        assert arr.dtype == np.float64, \
            f"Array dtype must be float64, but got {arr.dtype}"
        return arr.ctypes.data_as(POINTER(c_double))
    else:
        raise ValueError(
            f"Can not convert to POINTER(c_double). type is {type(arr)}")


def get_pointer64(arr, readonly: bool = False):
    """将NumPy数组转换为C语言双精度指针。

    Args:
        arr (Union[np.ndarray, Vector]): 输入数据容器，支持以下类型：
            - dtype为float64的NumPy数组
            - 包含pointer属性的Vector对象
        readonly: 是否返回只读指针，默认为False

    Returns:
        POINTER(c_double) or None: 指向连续内存的指针

    Raises:
        ValueError: 输入类型不匹配时抛出
        AssertionError: 当NumPy数组dtype不是float64时抛出
    """
    if readonly:
        return const_f64_ptr(arr)
    else:
        return f64_ptr(arr)


class SelfPath:
    """
    返回基于当前文件的路径
    """

    def __init__(self, this_file):
        self.this_dir = os.path.dirname(os.path.abspath(this_file))

    def __call__(self, *args, mkdir: bool = False) -> str:
        res = os.path.join(self.this_dir, *args)
        if isinstance(res, str):
            if mkdir:
                make_parent(res)
            return res
        else:
            return ""
