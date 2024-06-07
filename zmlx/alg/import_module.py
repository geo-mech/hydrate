import importlib
import os
import subprocess
import sys


def import_module(name, package=None, field=None, pip=None, show=None):
    """
    尝试导入一个外部的模块。 如果失败，则尝试通过pip来安装，之后，重新导入
    """
    try:  # 首次尝试导入
        m = importlib.import_module(name=name, package=package)
        return m if field is None else getattr(m, field)
    except:
        pass

    # Indicates whether the system is currently Windows (both Windows and Linux systems are currently supported)
    is_windows = os.name == 'nt'

    if pip is None or not is_windows:  # 仅Windows
        return

    try:  # 尝试使用pip来安装
        cmd = f'"{os.path.abspath(sys.executable)}" -m pip install {pip}'
        rc, out = subprocess.getstatusoutput(cmd)
        if show is not None:
            show(out)
        # 安装之后再次尝试导入
        m = importlib.import_module(name=name, package=package)
        return m if field is None else getattr(m, field)
    except:
        pass
