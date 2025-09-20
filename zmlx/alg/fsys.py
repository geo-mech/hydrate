"""
处理文件系统相关的操作
"""

import datetime
import os
import time


def list_files(path=None, keywords=None, exts=None):
    """
    列出给定路径下的所有的文件的路径。其中这些文件的完整路径中，应该包含所有给定的关键字 keywords
    另外，如果指定了扩展名exts，则将只在给定的这些文件类型中搜索
    """
    if path is None:
        path = os.getcwd()

    if os.path.isfile(path):
        try:
            is_ok = True
            if keywords is not None:
                for key in keywords:
                    if key not in path:
                        is_ok = False
                        break
            if is_ok:
                if exts is not None:
                    try:
                        ext = os.path.splitext(path)[1]
                        if ext not in exts:
                            is_ok = False
                    except:
                        is_ok = False
            if is_ok:
                return [path, ]
            else:
                return []
        except:
            return []
    elif os.path.isdir(path):
        files = []
        for name in os.listdir(path):
            files = files + list_files(os.path.join(path, name),
                                       keywords=keywords, exts=exts)
        return files
    else:
        return []


def list_code_files(path=None, exts=None):
    if exts is None:
        return list_files(path=path,
                          exts={'.h', '.hpp', '.c', '.cpp', '.py', '.pyw',
                                '.m'})
    else:
        return list_files(path=path, exts=exts)


def get_lines(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return len(file.readlines())
    except:
        return 0


def count_lines(path=None, exts=None):
    from zmlx.ui.gui_buffer import gui
    lines = 0
    for path in list_code_files(path=path, exts=exts):
        n = get_lines(path)
        lines += n
        print(f'{path}: {n}')
        gui.break_point()
    print(f'\n\nAll lines is: {lines}')


def first_only(path='please_delete_this_file_before_run'):
    """
    when it is executed for the second time, an exception is given to ensure that the result is not easily overwritten
    """
    from zmlx.ui import gui
    if os.path.exists(path):
        y = gui.question(
            'Warning: The existed data will be Over-Written. continue? ')
        if not y:
            assert False
    else:
        with open(path, 'w') as file:
            file.write('\n')


def get_last_file(folder):
    """
    返回给定文件夹中的最后一个文件（按照文件名，利用字符串默认的对比，从小到大排序）
    """
    if not os.path.isdir(folder):
        return None
    files = os.listdir(folder)
    if len(files) == 0:
        return None
    else:
        return os.path.join(folder, max(files))


def get_latest_file(folder):
    """
    获取指定文件夹内最新修改的文件的绝对路径

    参数：
        folder (str): 目标文件夹路径

    返回：
        str|None: 最新文件的绝对路径，异常时返回None
    """
    try:
        if not os.path.isdir(folder):
            return None

        latest_time = 0
        latest_path = None

        for entry in os.listdir(folder):
            full_path = os.path.join(folder, entry)
            if os.path.isfile(full_path):
                file_time = os.path.getmtime(full_path)
                if file_time > latest_time:
                    latest_time = file_time
                    latest_path = full_path

        return os.path.abspath(latest_path) if latest_path else None

    except:
        return None


def get_size_mb(path):
    """
    计算指定路径（文件或文件夹）的总大小，返回以MB为单位的浮点数

    参数：
        path (str): 目标路径（支持文件和文件夹）

    返回：
        float: 路径总大小（MB），异常时返回0.0
    """
    try:
        # 路径有效性验证（综合网页4、网页7的处理逻辑）
        if not os.path.exists(path):
            return 0.0

        # 区分文件/文件夹处理（参考网页9的类型判断）
        if os.path.isfile(path):
            # 单个文件处理（优化网页2的方案）
            return os.path.getsize(path) / (1024 * 1024)
        elif os.path.isdir(path):
            # 文件夹处理（继承原逻辑并优化）
            total_size = 0
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except (OSError, PermissionError):
                        continue
            return total_size / (1024 * 1024)
        else:
            # 特殊文件类型（如符号链接）
            return 0.0

    except:  # 统一异常处理（参考网页6的健壮性设计）
        return 0.0


def has_permission(folder):
    """
    是否有权限读取文件夹
    """
    try:
        os.listdir(folder)
        return True
    except:
        return False


def in_directory(file_name, directory):
    """
    判断给定的文件是否位于给定的路径或者其子目录下.
        by GPT 3.5. @2024-7-22
    """
    # 获取文件的绝对路径
    file_path = os.path.abspath(file_name)

    # 获取目录的绝对路径
    directory_path = os.path.abspath(directory)

    return file_path.startswith(directory_path)


def make_fname(time, folder=None, ext=None, unit=None):
    """
    根据给定的时间，生成一个文件名(或者一个文件路径)，用以存储文件;
    如果folder不存在，则此函数会自动创建这个folder
    如果folder为None，则返回None
    """
    if folder is None:
        return None
    name = ('%020.5f' % time).replace('.', '_')
    if unit is not None:
        name = name + unit
    if ext is not None:
        assert len(ext) >= 1
        if ext[0] == '.':
            name = name + ext
        else:
            name = name + '.' + ext
    if len(folder) > 0:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        name = os.path.join(folder, name)
    return name


def make_fpath(folder, step=None, ext='.txt', name=None):
    """
    Returns a filename to output data, and ensures that the folder exists
    """
    from zmlx.exts.base import make_dirs
    assert isinstance(folder, str)
    if not os.path.exists(folder):
        make_dirs(folder)
    else:
        assert os.path.isdir(folder)
    assert step is not None or name is not None
    if step is not None:
        return os.path.join(folder, f'{step:010d}{ext}')
    if name is not None:
        return os.path.join(folder, name)
    return None


def prepare_dir(folder, direct_del=False):
    """
    Prepare an empty folder for output calculation data
    """
    from zmlx.ui.gui_buffer import question
    from zmlx.exts.base import make_dirs
    if folder is None:
        return
    if os.path.exists(folder):
        if direct_del:
            y = True
        else:
            y = question(
                f'Do you want to delete the existed folder <{folder}>?')
        if y:
            import shutil
            shutil.rmtree(folder)
    if not os.path.exists(folder):
        make_dirs(folder)


def get_protected(func, res=None):
    def fx(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return res

    return fx


dirname = get_protected(os.path.dirname, None)
basename = get_protected(os.path.basename, None)
abspath = get_protected(os.path.abspath, None)

exists = get_protected(os.path.exists, False)
isdir = get_protected(os.path.isdir, False)
isfile = get_protected(os.path.isfile, False)

getsize = get_protected(os.path.getsize, 0)

getatime = get_protected(os.path.getatime, 0.0)
getmtime = get_protected(os.path.getmtime, 0.0)
getctime = get_protected(os.path.getctime, 0.0)

samefile = get_protected(os.path.samefile, False)
join_paths = get_protected(os.path.join, None)
join = get_protected(os.path.join, None)


def getsize_str(filename):
    """
    将文件的大小，显示为字符串
    """
    from zmlx.alg.base import fsize2str
    return fsize2str(getsize(filename))


def show_fileinfo(filepath):
    try:
        if isfile(filepath):
            print(f'File   Path: {filepath}')
            print(f'File   Size: {getsize_str(filepath)}')
            print(f'Access Time: {time.ctime(getatime(filepath))}')
            print(f'Modify Time: {time.ctime(getmtime(filepath))}')
            print('\n\n')
    except:
        pass


def now(*args, **kwargs):
    """
    Construct a datetime from time.time() and optional time zone info.
    """
    return datetime.datetime.now(*args, **kwargs)


def time_string():
    """
    生成一个时间字符串 (类似于 20201021T183800 这样的格式)
    """
    return now().strftime("%Y%m%dT%H%M%S")


def is_time_string(s):
    """
    check if the given string is a time string such as 20201021T183800.
    """
    if len(s) != 15:
        return False
    else:
        return s[0: 8].isdigit() and s[8] == 'T' and s[9: 15].isdigit()


def has_tag(folder=None):
    """
    Check if a file like 20201021T183800 exists
    """
    if folder is None:
        names = os.listdir(os.getcwd())
    else:
        if os.path.isdir(folder):
            names = os.listdir(folder)
        else:
            names = []
    for name in names:
        if is_time_string(name):
            return True
    return False


def print_tag(folder=None):
    """
    Print a file, the file name is similar to 20201021T183800, this file can be used as a label for the data,
    and then search the file to locate the data
    """
    from zmlx.exts.base import make_parent
    if has_tag(folder=folder):
        return
    if folder is None:
        path = time_string()
    else:
        path = os.path.join(folder, time_string())
    with open(make_parent(path), 'w') as file:
        file.write("data_tag\n")
        file.flush()


def _do_convert(i_path, o_path, convert=None, keep_file=True, create_data=None,
                index=None, count=None, t_beg=None):
    """
    执行转化过程. 返回是否成功
    """
    from zmlx.alg.base import time2str
    succeed = False
    try:
        if convert is not None:
            convert(i_path, o_path)
        else:
            data = create_data()
            data.load(i_path)
            data.save(o_path)
        succeed = True
    except:
        pass

    try:
        name = os.path.basename(o_path)
    except:
        name = o_path

    info = 'convert: '
    if index is not None and count is not None and t_beg is not None:
        assert 0 <= index < count
        t_used = (now() - t_beg).total_seconds()
        pct = (index + 1) / count
        t_left = t_used * (1 - pct) / pct
        info = f'{index + 1}/{count} ({time2str(t_used)} used, {time2str(t_left)} left): '

    if succeed:
        if not keep_file:
            try:
                if os.path.isfile(o_path):
                    os.remove(i_path)
            except:
                pass
        print(f'{info}"{i_path}" -> "{name}" Succeed!')
        return True
    else:
        print(f'{info}"{i_path}" -> "{name}" Failed!')
        return False


def change_fmt(convert=None, ext=None, path=None, keywords=None, keep_file=True,
               create_data=None, processes=None):
    """
    修改数据的格式。其中给定的函数<convert>将接受两个参数，分别为输入和输出的路径
    """
    from zmlx.alg.multi_proc import apply_async, create_async
    from zmlx.alg.base import time2str
    if ext is None:
        print('You must set the new file extension')
        return
    files = list_files(path=path, keywords=keywords)
    tasks = []
    t_beg = now()
    for idx in range(len(files)):
        file = files[idx]
        portion = os.path.splitext(file)
        assert len(portion) == 2
        opath = portion[0] + ext
        tasks.append(create_async(
            func=_do_convert,
            kwds={'i_path': file, 'o_path': opath,
                  'convert': convert,
                  'create_data': create_data,
                  'keep_file': keep_file,
                  'index': idx,
                  'count': len(files), 't_beg': t_beg
                  }))
    is_succeed = apply_async(tasks=tasks, processes=processes)

    assert len(is_succeed) == len(files)
    fails = []
    for idx in range(len(is_succeed)):
        if not is_succeed[idx]:
            fails.append(files[idx])
    if len(fails) == 0:
        print(
            f'\nAll succeed! (time used = {time2str((now() - t_beg).total_seconds())})')
    else:
        print('\n')
        for file in fails:
            print(f'Convert failed: "{file}"')
        print(
            f'Count of fail = {len(fails)}. (time used = {time2str((now() - t_beg).total_seconds())})')
