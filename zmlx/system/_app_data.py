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

    def set(self, key: Union[str, int], value: Any):
        """存储数据到内存空间。

        Args:
            key (str | int): 数据标识符
            value (Any): 要存储的值

        Note:
            - 支持任意Python对象存储
            - 数据仅存在于运行时内存中
        """
        self.space[key] = value

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


# 应用数据管理器实例
app_data = _AppData()
