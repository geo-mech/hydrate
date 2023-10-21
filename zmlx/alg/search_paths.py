import os

from zml import app_data, gui


def get_paths():
    try:
        paths = []
        for line in app_data.getenv(key='path', default='').splitlines():
            line = line.strip()
            if os.path.isdir(line):
                paths.append(line)
        return paths
    except:
        return []


def add_path(paths, path):
    for existed in paths:
        if os.path.samefile(existed, path):
            return
    paths.append(path)


def save_paths(paths):
    try:
        app_data.setenv('path', '\n'.join(paths))
    except:
        pass


def choose_path():
    folder = gui.get_existing_directory('请选择文件夹', os.getcwd())
    if len(folder) > 0 and os.path.isdir(folder):
        try:
            paths = get_paths()
            add_path(paths, folder)
            save_paths(paths)
            gui.information('成功', f'成功添加了搜索路径: \n<{folder}> \n\n下次启动软件时生效!')
        except Exception as e:
            print(e)
