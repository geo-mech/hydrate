import os
import sys

from zmlx.alg.base import clamp
from zmlx.system import app_data, get_hash, read_text


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


def _path(*args):
    return os.path.join(os.path.dirname(__file__), *args)


def _files():
    folder = os.path.dirname(__file__)
    files = []
    for name in os.listdir(folder):
        if name.endswith('.py'):
            if name != '__init__.py' and name != '_alg.py':
                files.append(_path(name))
    return files


def get_files(rank_max=2.0e10):
    """
    返回所有的，经过排序的，存在的，去除重复的，zml_gui_setup.py文件的路径。
    如果给定rank_max，则只返回rank小于等于rank_max的文件。
    """
    from zmlx.alg.sys import listdir

    all_files = []

    try:
        for path in _files():
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
    try:
        from zmlx.scen import get_path
        folders.append(get_path())  # 附加scen文件夹
    except:
        pass
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


def run_setup():
    """
    设置GUI的额外的选项
    """
    from zmlx.ui import gui
    the_logs = []
    for path in get_files():
        try:
            folder = os.path.dirname(os.path.dirname(path))
            if folder not in sys.path:
                sys.path.append(folder)  # 确保包含zml_gui_setup.py的包能够被正确import

            the_logs.append(f'Exec File: {path}')
            # 备份app_data
            name = app_data.space.get('__name__', None)
            file = app_data.space.get('__file__', None)
            # 针对此文件，设置name和file
            app_data.space['__name__'] = '__main__'
            app_data.space['__file__'] = path
            # 运行此文件
            try:
                exec(read_text(path, encoding='utf-8'), app_data.space)
                error = None
            except Exception as e:
                error = e
            # 恢复app_data
            app_data.space['__name__'] = name
            app_data.space['__file__'] = file
            # 处理错误
            if error is not None:
                raise error
        except Exception as err:
            the_logs.append(f'Failed: {err}')
            gui.add_message(f'path = {path}, error = {err}')
    app_data.put('gui_setup_logs', the_logs)
