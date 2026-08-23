"""搜索路径管理（增删查改搜索路径列表）.

Modified by Claude, 2026-08-12
"""

import os


def get_paths():
    """返回当前搜索路径列表。"""
    try:
        from zmlx.exts import app_data
        paths = []
        for line in app_data.getenv(key='path', default='').splitlines():
            line = line.strip()
            if os.path.isdir(line):
                paths.append(line)
        return paths
    except Exception:
        return []


def add_path(paths, path):
    for existed in paths:
        if os.path.samefile(existed, path):
            return
    paths.append(path)


def save_paths(paths):
    """保存搜索路径列表。"""
    try:
        from zmlx.exts import app_data
        app_data.setenv('path', '\n'.join(paths))
    except Exception:
        pass


def choose_path():
    """弹出对话框让用户选择路径。"""
    from zmlx.ui import gui
    if not gui.exists():
        return
    folder = gui.get_existing_directory('请选择文件夹', os.getcwd())
    if len(folder) > 0 and os.path.isdir(folder):
        try:
            paths = get_paths()
            add_path(paths, folder)
            save_paths(paths)
            gui.information('成功',
                            f'成功添加了搜索路径: \n<{folder}> \n\n下次启动软件时生效!')
        except Exception as e:
            print(e)
