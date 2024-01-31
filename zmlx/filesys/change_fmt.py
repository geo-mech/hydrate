import os
import sys
from datetime import datetime

from zml import Seepage
from zmlx.alg.apply_async import apply_async, create_async
from zmlx.alg.time2str import time2str
from zmlx.filesys.list_files import list_files


def do_convert(i_path, o_path, convert=None, keep_file=True, create_data=None,
               index=None, count=None, t_beg=None):
    """
    执行转化过程. 返回是否成功
    """
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
        t_used = (datetime.now() - t_beg).total_seconds()
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
    if ext is None:
        print('You must set the new file extension')
        return
    files = list_files(path=path, keywords=keywords)
    tasks = []
    t_beg = datetime.now()
    for idx in range(len(files)):
        file = files[idx]
        portion = os.path.splitext(file)
        assert len(portion) == 2
        opath = portion[0] + ext
        tasks.append(create_async(func=do_convert,
                                  kwds={'i_path': file, 'o_path': opath, 'convert': convert,
                                        'create_data': create_data, 'keep_file': keep_file,
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
        print(f'\nAll succeed! (time used = {time2str((datetime.now() - t_beg).total_seconds())})')
    else:
        print('\n')
        for file in fails:
            print(f'Convert failed: "{file}"')
        print(f'Count of fail = {len(fails)}. (time used = {time2str((datetime.now() - t_beg).total_seconds())})')


def seepage2txt(path=None, processes=None):
    """
    将seepage文件转化为txt （注意，文件必须存储在models中）
    """
    if path is None:
        path = os.getcwd()
    change_fmt(path=path, ext='.txt', keywords=['.seepage', 'models'], keep_file=False, create_data=Seepage,
               processes=processes)


def txt2seepage(path=None, processes=None):
    """
    将txt文件转化为seepage （注意，文件必须存储在models中）
    """
    if path is None:
        path = os.getcwd()
    change_fmt(path=path, ext='.seepage', keywords=['.txt', 'models'], keep_file=False, create_data=Seepage,
               processes=processes)


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        key = sys.argv[1]
        path = None
        if len(sys.argv) >= 3:
            path = sys.argv[2]
        if key == 'seepage2txt':
            seepage2txt(path)

        if key == 'txt2seepage':
            txt2seepage(path)
