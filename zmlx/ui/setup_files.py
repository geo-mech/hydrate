import os

from zmlx.alg.base import clamp
from zmlx.exts.base import app_data, get_hash


def get_rank(path):
    """
    返回配置文件的优先级
    """
    if not isinstance(path, str):
        return 1.0e20
    try:
        text = app_data.getenv(key=get_hash('rank: ' + path))
        rank = float(text)
        return clamp(rank, 0.0, 1.0e20)
    except TypeError:  # 默认的rank
        return 1.0e10


def set_rank(path, rank=None):
    """
    修改配置文件的优先级
    """
    if not isinstance(rank, (int, float)):
        rank = 1.0e10  # 重置为默认的rank
    else:
        rank = clamp(rank, 0.0, 1.0e20)
    app_data.setenv(
        key=get_hash('rank: ' + path), value=f'{rank}')


def get_files(rank_max=2.0e10):
    """
    返回所有的，经过排序的，存在的，去除重复的，zml_gui_setup.py文件的路径。
    如果给定rank_max，则只返回rank小于等于rank_max的文件。
    """
    from zmlx.alg.sys import listdir

    all_files = []

    try:
        from zmlx.ui.exts import get_files
        for path in get_files():
            if os.path.isfile(path) and path not in all_files:
                all_files.append(path)
    except Exception as err:
        print(err)

    # 用户额外存储的文件
    files_data = app_data.getenv(
        key='zml_gui_setup_files', encoding='utf-8', default=''
    )
    for f in files_data.split(';'):
        try:
            path = os.path.abspath(f.strip())
            if os.path.isfile(path) and path not in all_files:
                all_files.append(path)
        except Exception as err:
            print(err)

    # 在程序包内搜索到的文件
    folders = app_data.get_paths()
    folders.extend(listdir(path=folders, with_file=False, with_dir=True))
    for folder in folders:
        path = os.path.abspath(os.path.join(folder, 'zml_gui_setup.py'))
        if os.path.isfile(path) and path not in all_files:
            all_files.append(path)

    # 附加优先级
    file_ranks = []
    for path in all_files:
        rank = get_rank(path)
        if rank <= rank_max:
            file_ranks.append([path, rank])

    # 根据rank来排序
    file_ranks.sort(key=lambda x: x[1])

    # 返回所有的文件名
    return [file_rank[0] for file_rank in file_ranks]


def set_files(files):
    """
    保存当前列表到环境变量
    """
    files = [os.path.abspath(file) for file in files]

    # 存储列表
    app_data.setenv(
        key='zml_gui_setup_files',
        encoding='utf-8',
        value=";".join(files)
    )

    # 确保不在列表中的文件会被排除
    for file in get_files(rank_max=1.0e200):
        if file not in files:
            set_rank(file, 1.0e20)

    # 存储列表的rank
    for idx in range(len(files)):
        set_rank(files[idx], idx + 1)
