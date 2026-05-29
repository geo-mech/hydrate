import os
import subprocess


def startfile(path):
    """
    打开文件
    Args:
        path: 文件路径
    """
    from zmlx.exts import in_linux, in_windows, in_macos
    if in_windows():
        os.startfile(path)
    elif in_linux():
        subprocess.run(['xdg-open', path], check=True)
    elif in_macos():
        subprocess.run(['open', path], check=True)


def test():
    from zmlx.io.path import opath
    startfile(opath())


if __name__ == '__main__':
    test()
