import os

from zmlx.filesys.list_files import list_files
from zmlx.alg.apply_async import apply_async, create_async
from zml import Seepage


def do_convert(i_path, o_path, convert=None, keep_file=True, create_data=None, index=None):

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
    if succeed:
        if not keep_file:
            if os.path.isfile(o_path):
                os.remove(i_path)
        print(f'convert ({index}): "{i_path}" -> "{o_path}" Succeed!')
    else:
        print(f'convert ({index}): "{i_path}" -> "{o_path}" Failed!')


def change_fmt(convert=None, ext=None, path=None, keywords=None, keep_file=True, create_data=None):
    """
    修改数据的格式。其中给定的函数<convert>将接受两个参数，分别为输入和输出的路径
    """
    if ext is None:
        print('You must set the new file extension')
        return
    files = list_files(path=path, keywords=keywords)
    tasks = []
    for idx in range(len(files)):
        file = files[idx]
        portion = os.path.splitext(file)
        assert len(portion) == 2
        opath = portion[0] + ext
        tasks.append(create_async(func=do_convert,
                                  kwds={'i_path': file, 'o_path': opath, 'convert': convert,
                                        'create_data': create_data, 'keep_file': keep_file,
                                        'index': f'{idx}/{len(files)}'}))
    apply_async(tasks=tasks)


def seepage2txt(path=None):
    """
    将seepage文件转化为txt （注意，文件必须存储在models中）
    """
    if path is None:
        path = os.getcwd()
    change_fmt(path=path, ext='.txt', keywords=['.seepage', 'models'], keep_file=False, create_data=Seepage)


def txt2seepage(path=None):
    """
    将txt文件转化为seepage （注意，文件必须存储在models中）
    """
    if path is None:
        path = os.getcwd()
    change_fmt(path=path, ext='.seepage', keywords=['.txt', 'models'], keep_file=False, create_data=Seepage)
