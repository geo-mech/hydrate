"""
处理系统相关的操作。后续修改的时候需要保证：
    此模块应不依赖于任何第三方模块，以及不依赖于zml
"""
import importlib
import os
import shutil
import subprocess
import sys
import time
import timeit
import warnings


def log_deprecated(name):
    """
    记录一个弃用模块的使用
    Args:
        name: 弃用模块或者函数的名字

    Returns:
        None
    """
    from zml import log
    log(f'The deprecated used: {name}', tag=f'{name}.deprecated_used')


def warn(message, category=None, stacklevel=1, tag=None):
    """
    警告，并且当tag给定的时候，则记录日志 (每天只记录一次)
    Args:
        tag: 记录日志的标签
        message: 需要弹出的警告
        category: 类别
        stacklevel: 栈的深度

    Returns:
        None
    """
    warnings.warn(message=message, category=category, stacklevel=stacklevel + 1)
    if tag is None:
        tag = message
    if isinstance(tag, str):
        from zml import log
        log(text=message, tag=f'{tag}.warn')


def type_assert(o, dtype):
    """
    类型断言

    断言给定的数据o是给定的类型dtype. 相对于assert isinstance，使用这个函数，可以显示错误。
    但是，使用此函数，PyCharm无法识别o的类型，从而无法给出类型提示.
    """
    warnings.warn(f'type_assert function will be removed after 2026-4-15',
                  DeprecationWarning,
                  stacklevel=2)
    assert isinstance(o, dtype), (f'type assert failed: {dtype} required, '
                                  f'but {type(o)} with value = {o} is given')


def timing_show(key, func, *args, **kwargs):
    """
    执行函数，并且显示执行的耗时. 主要用于模型初始化过程中，显示那些耗时的操作

    Args:
        key: 操作的名字
        func: 操作的函数
        *args: 操作的参数
        **kwargs: 操作的参数
    Returns:
        操作的结果
    """
    print(f'{key} ... ', end='')
    t_beg = timeit.default_timer()
    res = func(*args, **kwargs)
    t_end = timeit.default_timer()
    print(' succeed. time used = %.2f s' % (t_end - t_beg))
    return res


def sbatch(*args, c=1, t=None, p='G1Part_sce', job=None):
    """
    在北京超算上面创建一个任务. 其中:
        args: 跟在python后面的参数.
        c: 调用的核心的数量
        t: 休眠时间(当启动多个的时候，加上休眠，确保多个任务不要同时启动)
    """
    if len(args) == 0:
        return
    text = f"""#!/bin/bash
#SBATCH  -n 1
#SBATCH  -c {c}
srun     -n 1  -c {c}  python3 """
    for arg in args:
        text = text + f' {arg}'
    if job is None:
        job = 'jb'
    name = None
    for i in range(100000):
        x = f'{job}{i}.sh'
        if not os.path.exists(x):
            name = x
            break
    assert name is not None
    with open(name, 'w') as file:
        file.write(text)
        file.write('\n')
        file.flush()
    os.system(f"sbatch -p {p} {name}")
    print(f'task submitted: {args}')
    if t is not None:
        time.sleep(t)


def py2pyc(ipath: str, opath: str):
    """
    编译py文件(对于非py文件，则简单复制).

    Args:
        ipath: 输入的路径
        opath: 输出的路径

    Returns:
        None
    """

    if os.path.isfile(ipath):  # 对于Python文件，执行编译操作;
        assert ipath.endswith('.py') and opath.endswith('.pyc')
        try:
            import py_compile
            folder = os.path.dirname(opath)
            if not os.path.isdir(folder):
                os.makedirs(folder, exist_ok=True)
            py_compile.compile(ipath, cfile=opath)
            print(f"Succeed: {ipath} -> {opath}")
        except Exception as e:
            print(f"Failed: {ipath}. {e}")

    elif os.path.isdir(ipath):  # 对于目录，则遍历执行
        for name in os.listdir(ipath):
            path = os.path.join(ipath, name)
            if os.path.isfile(path):  # 对于文件
                if name.endswith('.py'):  # 对于Python文件，则尝试编译
                    py2pyc(ipath=path, opath=os.path.join(opath, name + 'c'))
                else:  # 对于普通的文件，则尝试拷贝
                    try:
                        if not os.path.isdir(opath):
                            os.makedirs(opath, exist_ok=True)
                        if not os.path.samefile(ipath, opath):
                            shutil.copy(path, os.path.join(opath, name))
                            print(
                                f"Succeed: {path} -> {os.path.join(opath, name)}")
                    except Exception as e:
                        print(f"Failed: {path}. {e}")
            elif os.path.isdir(path):  # 对于路径，则递归执行
                if name != '__pycache__' and name != '.git':  # 忽略缓存目录
                    py2pyc(ipath=path, opath=os.path.join(opath, name))
                else:
                    print(f'Ignore: {path}')


def pip_install(package_name, name=None, show_exists=True):
    """使用pip安装指定的Python包。

    如果提供了name参数，会先检查该模块是否已存在，只有在模块不存在时才会安装package_name。

    Args:
        show_exists: 在包已经存在的时候，是否显示提示信息。
        package_name (str): 要安装的Python包名称。
        name (str, optional): 要检查的模块名称。如果为None，则直接安装package_name。

    Returns:
        None
    """
    try:
        if name is not None:
            from importlib.util import find_spec
            if find_spec(name):
                if show_exists:
                    print(f"安装包 {package_name} 已经存在!")
                return
        subprocess.check_call([f'{os.path.abspath(sys.executable)}',
                               '-m', 'pip', 'install',
                               package_name])
    except subprocess.CalledProcessError as e:
        print(f"安装包 {package_name} 失败: {e}")


def install_dep(show_exists=True):
    """
    安装计算模块运行所需要的第三方的包
    """
    found_qt = False
    if not found_qt:
        try:
            import PyQt6
            found_qt = True
            pip_install('PyQt6-WebEngine', 'PyQt6.QtWebEngineWidgets',
                        show_exists=show_exists)
            pip_install('pyqt6-qscintilla', 'PyQt6.Qsci',
                        show_exists=show_exists)
        except:
            pass

    if not found_qt:
        try:
            import PyQt5
            found_qt = True
            pip_install('PyQtWebEngine', 'PyQt5.QtWebEngineWidgets',
                        show_exists=show_exists)
        except:
            pass

    if not found_qt:
        if sys.version_info >= (3, 8):
            items = [('PyQt6', 'PyQt6'),
                     ('PyQt6-WebEngine', 'PyQt6.QtWebEngineWidgets'),
                     ('pyqt6-qscintilla', 'PyQt6.Qsci')
                     ]
        else:
            items = [('PyQt5', 'PyQt5'),
                     ('PyQtWebEngine', 'PyQt5.QtWebEngineWidgets')
                     ]
        for package_name, name in items:
            pip_install(package_name, name=name, show_exists=show_exists)

    for package_name, name in [
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib'),
        ('PyOpenGL', 'OpenGL'),
        ('pyqtgraph', 'pyqtgraph'),
        ('pypiwin32', 'win32com'),
        ('pywin32', 'pywintypes'),
        ('dulwich', 'dulwich'),
    ]:
        pip_install(package_name, name=name, show_exists=show_exists)


def add_pth_file(name, folder):
    """
    Add the current folder to python's search path

    Args:
        name: the name of the pth file
        folder: the folder to add
    Returns:
        None
    """
    pth = os.path.join(os.path.dirname(sys.executable), name)
    if not os.path.isdir(folder):
        return
    if os.path.isfile(pth):
        with open(pth, 'r') as file:
            text = file.read()
            if os.path.isdir(text):
                if os.path.samefile(folder, text):
                    return
    with open(pth, 'w') as file:
        file.write(folder)
    print(f"Succeed Installed: '{folder}' \n       --> '{pth}'")


def import_module(name, package=None, field=None, pip=None, show=None):
    """
    尝试导入一个外部的模块。 如果失败，则尝试通过pip来安装，之后，重新导入

    Args:
        name: 模块的名字
        package: 包的名字
        field: 字段的名字
        pip: 安装的名字
        show: 显示的函数
    Returns:
        None
    """
    try:  # 首次尝试导入
        m = importlib.import_module(name=name, package=package)
        return m if field is None else getattr(m, field)
    except:
        pass

    # Indicates whether the system is currently Windows (both Windows and Linux systems are currently supported)
    is_windows = os.name == 'nt'

    if pip is None or not is_windows:  # 仅Windows
        return None

    try:  # 尝试使用pip来安装
        cmd = f'"{os.path.abspath(sys.executable)}" -m pip install {pip}'
        rc, out = subprocess.getstatusoutput(cmd)
        if show is not None:
            show(out)
        # 安装之后再次尝试导入
        m = importlib.import_module(name=name, package=package)
        return m if field is None else getattr(m, field)
    except:
        return None


def get_desktop_path(*args):
    """
    返回本机Desktop文件夹的路径
    """
    warn(f'The zmlx.alg.sys.get_desktop_path is deprecated '
         f'and will be removed after 2026-5-16, please use '
         f'zmlx.alg.os.get_desktop_path instead.',
         DeprecationWarning, stacklevel=2)
    from zmlx.alg.os import get_desktop_path as impl
    return impl(*args)


def get_pythonw_path():
    """
    获取pythonw.exe的路径
    Args:
    Returns:
        str: pythonw.exe的路径
    """
    # 获取当前Python解释器的路径（通常是python.exe的路径）
    python_exe = sys.executable
    # 构造pythonw.exe的路径（与python.exe同目录）
    directory = os.path.dirname(python_exe)
    pythonw_exe = os.path.join(directory, "pythonw.exe")

    # 检查pythonw.exe是否存在
    if os.path.exists(pythonw_exe):
        return pythonw_exe
    else:
        return python_exe


def get_latest_version():
    """
    返回程序的最新的版本.
    Returns:
        int: 版本号
    """
    warnings.warn('function get_latest_version deprecated',
                  DeprecationWarning, stacklevel=2)
    return 100101  # default


def create_shortcut(target: str, path: str,
                    arguments: str = "",
                    working_dir: str = None,
                    icon_path: str = None,
                    description: str = "Python Shortcut"):
    """
    在指定路径创建指向目标的Windows快捷方式

    参数:
        target (str): 目标文件/程序的完整路径
        path (str): 快捷方式保存路径（需包含.lnk扩展名）
        arguments (str): 启动参数（可选）
        working_dir (str): 工作目录（默认目标所在目录）
        icon_path (str): 图标文件路径（可选）
        description (str): 快捷方式描述（可选）
    """
    try:
        from pathlib import Path
        import win32com.client  # pip_install('pypiwin32')

        # 验证目标路径是否存在
        if not Path(target).exists():
            raise FileNotFoundError(f"目标文件不存在: {target}")

        # 确保保存路径包含.lnk扩展名
        path = str(Path(path).with_suffix('.lnk'))

        # 创建父目录（如果不存在）
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # 创建快捷方式对象
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)

        # 设置基本属性
        shortcut.TargetPath = str(Path(target).resolve())
        shortcut.Arguments = arguments
        shortcut.Description = description

        # 设置工作目录（优先使用参数，否则取目标所在目录）
        if working_dir:
            shortcut.WorkingDirectory = str(Path(working_dir).resolve())
        else:
            shortcut.WorkingDirectory = str(Path(target).parent.resolve())

        # 设置自定义图标
        if icon_path and Path(icon_path).exists():
            shortcut.IconLocation = str(Path(icon_path).resolve())

        # 保存快捷方式
        shortcut.save()
        print(f"快捷方式已创建于：{path}")

    except Exception as e:
        raise RuntimeError(f"创建快捷方式失败: {str(e)}") from e


def create_ui_lnk_on_desktop(name='IGG-Hydrate.lnk'):
    """
    在桌面创建一个指向zml_ui.pyw的快捷方式
    Args:
        name: 快捷方式的名字

    Returns:
        None
    """
    from zmlx.alg.os import get_desktop_path
    from zmlx import get_path
    filename = get_desktop_path(name)
    if isinstance(filename, str):
        create_shortcut(get_pythonw_path(), filename,
                        arguments=get_path('..', 'zml_ui.pyw')
                        )


def has_module(name):
    """
    测试是否存在给定名字的库
    """
    try:
        import importlib
        importlib.import_module(name)
        return True
    except:
        return False


def get_ipinfo():
    """
    返回当前主机的IP信息
    """
    import http.client
    import json
    conn = http.client.HTTPSConnection("ipinfo.io")
    conn.request("GET", "/json")
    response = conn.getresponse()
    data = response.read().decode()
    conn.close()
    info = json.loads(data)
    return info


def get_city():
    """
    获得当前主机的位置(具体到城市)
    """
    info = get_ipinfo()
    return info.get('city', 'error') + ', ' + info.get('country', 'error')


def create_deprecated(pack_name, func, date=None):
    """
    创建一个弃用的函数
    """
    return dict(pack_name=pack_name, func=func, date=date)


def get_deprecated(name, data, current_pack_name):
    """
    当访问不存在的属性时，尝试从其他模块中导入
    """
    import importlib
    value = data.get(name)
    if value is not None:
        pack_name = value.get('pack_name')
        func = value.get('func')
        date = value.get('date')
        warnings.warn(
            f'<{current_pack_name}.{name}> will be removed after {date}, '
            f'please use <{pack_name}.{func}> instead.',
            DeprecationWarning,
            stacklevel=2
        )
        mod = importlib.import_module(pack_name)
        return getattr(mod, func)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def srand(seed):
    """
    设置Python和zml内核的随机数种子.  2023-9-25
    """
    import random
    from zml import set_srand

    random.seed(seed)
    set_srand(seed)
