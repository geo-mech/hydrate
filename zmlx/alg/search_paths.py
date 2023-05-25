# -*- coding: utf-8 -*-


import os
from zml import app_data, gui

filepath = app_data.temp('zml_search_paths')


def get_paths():
    try:
        paths = []
        with open(filepath, 'r') as file:
            for line in file.readlines():
                paths.append(line.strip())
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
        with open(filepath, 'w') as file:
            for path in paths:
                file.write(f'{path}\n')
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

