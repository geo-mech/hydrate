import os
import sys


def get_pythonw_path():
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


if __name__ == '__main__':
    print(get_pythonw_path())
