# ** name = '零碎文件处理'
# ** desc = '把工作路径下的散落文件压缩成 zip，或把 zip 解压回工作路径（会显著改动文件结构，执行前二次确认）'
# ** enabled = False
"""文件打包/解包工具（将散落文件 zip 或 unzip）—— 菜单「操作 → 零碎文件处理」.

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-18: 菜单由「帮助 → 零碎文件处理」移到「操作」下
    （压缩/解压是对工作路径的实际动作，与「运行/停止」同属一类）
"""

import os
import zipfile

from zmlx.algs.fsys import is_time_string
from zmlx.system import execute_once
from zmlx.ui.gui_buffer import gui

dataname = 'zml_files.zip'


def execute_zip(folder, this_only=False):
    """
    将folder中比较零碎的文件压缩到一个zip文件中，方便存储
    """
    gui.break_point()
    if not os.path.isdir(folder):
        return
    if this_only:
        if os.path.isfile(os.path.join(folder, dataname)):
            return
        all = []
        fs_all = 0
        try:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if name == dataname or is_time_string(name):
                    continue
                if not os.path.isfile(path):
                    continue
                # if os.path.samefile(__file__, path):
                #     continue
                fs = os.path.getsize(path) / 1024.0 ** 2
                if fs > 200:
                    continue
                else:
                    all.append((name, path))
                    fs_all += fs
        except Exception as e:
            print(f'Error: {e}')
            all = []
        if len(all) < 2:
            return
        if fs_all > 10000 or fs_all / len(all) > 50:
            return
        try:
            print(f'Zip {folder} ... ', end='', flush=True)
            z = zipfile.ZipFile(os.path.join(folder, dataname), 'w',
                                zipfile.ZIP_DEFLATED)
            for name, path in all:
                z.write(filename=path, arcname=name)
            z.close()
            for name, path in all:
                os.remove(path)
        except Exception:
            print('Failed')
        else:
            print('Succeed')
    else:
        try:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if os.path.isdir(path):
                    execute_zip(path, this_only=False)
            execute_zip(folder, this_only=True)
        except KeyboardInterrupt:
            return
        except Exception:
            pass


def execute_unzip(folder, this_only=False):
    """
    将folder中的zip文件解压
    """
    gui.break_point()
    if not os.path.isdir(folder):
        return
    if this_only:
        file = os.path.join(folder, dataname)
        if os.path.isfile(file):
            try:
                print(f'Unzip {file} ... ', end='', flush=True)
                z = zipfile.ZipFile(file, 'r')
                z.extractall(folder)
                z.close()
                os.remove(file)
            except Exception:
                print('Failed')
            else:
                print('Succeed')
        all = []
        try:
            for name in os.listdir(folder):
                parts = os.path.splitext(name)
                ext = parts[-1]
                if ext != '.zip':
                    continue
                path = os.path.join(folder, name)
                if not os.path.isfile(path):
                    continue
                log = os.path.join(folder, parts[0] + '.log')
                if not os.path.isfile(log):
                    continue
                else:
                    all.append((parts[0], log, path))
        except Exception:
            all = []

        for subdir, log, path in all:
            try:
                print(f'Unzip {path} ... ', end='', flush=True)
                z = zipfile.ZipFile(path, 'r')
                z.extractall(os.path.join(folder, subdir))
                z.close()
                os.remove(path)
                os.remove(log)
            except Exception:
                print('Failed')
            else:
                print('Succeed')
    else:
        try:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if os.path.isdir(path):
                    execute_unzip(path, this_only=False)
            execute_unzip(folder, this_only=True)
        except KeyboardInterrupt:
            return
        except Exception:
            pass


@execute_once(file=__file__)
def setup_ui():
    """把「压缩」「解压」直接挂到「**操作 → 零碎文件处理**」下.

    ⚠️ **菜单在「操作」而不是「帮助」**（2026-10-18 移）：压缩 / 解压是**对工作路径
    的实际动作**（会改动文件结构），与「操作」里那些「运行 / 停止 / 保存」是一类；
    放在「帮助」下面纯属历史遗留。

    ⚠️ **不再有「加载 → 零碎文件处理」那一级**：本文件是插件，插件一旦被执行，
    菜单就该**当场出现** —— 让用户再点一次「加载」才生成子菜单，是把装配层的旧
    习惯带了过来，插件没有这个必要。
    """

    def func1():
        if not gui.question(
                f'危险操作：\n\n会将当前目录下({os.getcwd()})的零碎文件压缩到一个'
                f'zip文件中，并显著修改文件结构. \n\n是否继续？'):
            return
        execute_zip(os.getcwd())

    gui.add_action(
        menu=['操作', '零碎文件处理'], text='压缩', slot=lambda: gui.start(func1),
    )

    def func2():
        if not gui.question(
                f'危险操作：\n\n会将当前目录下({os.getcwd()})的zip文件解压，'
                f'并显著修改文件结构. \n\n是否继续？'):
            return
        execute_unzip(os.getcwd())

    gui.add_action(
        menu=['操作', '零碎文件处理'], text='解压', slot=lambda: gui.start(func2),
    )


# ⚠️ 插件的标准形式：**注册写在这个分支里**。
#    插件机制用 ``exec`` 执行本文件时，命名空间里的 ``__name__`` 被设成
#    ``'__zml_plugin__'``，于是这里成立 —— 只注册，不开窗口。
#
#    ⚠️ **不要**在顶层裸写 ``setup_ui()``（本文件 2026-10-22 之前就是这样）：
#       · 那样「插件加载」与「直接运行本文件」走同一段代码，无法区分两种意图；
#       · 也无法在这里加 ``__main__`` 分支做自测 —— 顶层那行会先执行。
#    另外：``gui.add_action`` 在没有界面时本来就不做事（见 ``gui_buffer.add_action``
#    的 ``if gui.exists()``），所以无头环境下注册是无害的；套了
#    ``@execute_once``，重复执行也不会重复注册。
if __name__ == '__zml_plugin__':
    setup_ui()
