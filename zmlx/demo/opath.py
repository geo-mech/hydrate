# ** desc = '设置demo算例计算结果存储的主目录'

from zmlx.filesys import opath as op
from zmlx.ui import gui


def information(*args, **kwargs):
    if gui.exists():
        gui.information(*args, **kwargs)


def set_output(folder=None):
    """
    设置demo执行的输出路径
    """
    op.set_opath(folder=folder, key='demo_output')


def opath(*args):
    """
    返回输出目录 (如果不成功，则返回None)
    """
    return op.opath(*args, key='demo_output')


def main():
    """
    设置demo的输出目录
    """
    if gui.exists():
        root = opath()
        name = gui.get_existing_directory('Choose Demo Output Folder', root)
        if len(name) > 0:
            set_output(name)
        else:
            print(f'Current folder: {root}')


if __name__ == '__main__':
    gui.execute(func=main, close_after_done=False)
