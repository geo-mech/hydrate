import os
import zipfile

from zmlx.alg.fsys import is_time_string
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
        except:
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
        except:
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
            except:
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
        except:
            all = []

        for subdir, log, path in all:
            try:
                print(f'Unzip {path} ... ', end='', flush=True)
                z = zipfile.ZipFile(path, 'r')
                z.extractall(os.path.join(folder, subdir))
                z.close()
                os.remove(path)
                os.remove(log)
            except:
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
        except:
            pass


def setup_ui():
    def func1():
        if not gui.question(f'危险操作：\n\n会将当前目录下({os.getcwd()})的零碎文件压缩到一个zip文件中，并显著修改文件结构. \n\n是否继续？'):
            return
        execute_zip(os.getcwd())

    gui.add_action(
        menu=['帮助', '零碎文件处理'], text='压缩', slot=lambda: gui.start(func1),
    )

    def func2():
        if not gui.question(f'危险操作：\n\n会将当前目录下({os.getcwd()})的zip文件解压，并显著修改文件结构. \n\n是否继续？'):
            return
        execute_unzip(os.getcwd())

    gui.add_action(
        menu=['帮助', '零碎文件处理'], text='解压', slot=lambda: gui.start(func2),
    )


def main():
    from zmlx.alg.sys import first_execute
    if first_execute(__file__):
        gui.execute(func=setup_ui, keep_cwd=False, close_after_done=False)


if __name__ == '__main__':
    main()
