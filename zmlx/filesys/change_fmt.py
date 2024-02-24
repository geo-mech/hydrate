import os

from zmlx.filesys.list_files import list_files


def change_fmt(convert=None, ext=None, path=None, keywords=None, keep_file=True, create_data=None):
    """
    修改数据的格式。其中给定的函数<convert>将接受两个参数，分别为输入和输出的路径
    """
    if ext is None:
        print('You must set the new file extension')
        return
    if convert is None:
        if create_data is not None:
            def convert(i, o):
                data = create_data()
                data.load(i)
                data.save(o)
        else:
            print('You must set either the kernel <func> or the class <type>')
            return

    assert convert is not None

    files = list_files(path=path, keywords=keywords)
    for file in files:
        portion = os.path.splitext(file)
        assert len(portion) == 2
        opath = portion[0] + ext
        try:
            print(f'Convert {file} to {opath} .. ', end='')
            convert(file, opath)
            if not keep_file:
                os.remove(file)
        except Exception as err:
            print(f'Failed. error = {err}')
        else:
            print('Succeed!')


def seepage2txt(path=None):
    """
    将seepage文件转化为txt （注意，文件必须存储在models中）
    """
    from zml import Seepage
    if path is None:
        path = os.getcwd()
    change_fmt(path=path, ext='.txt', keywords=['.seepage', 'models'], keep_file=False, create_data=Seepage)


def txt2seepage(path=None):
    """
    将txt文件转化为seepage （注意，文件必须存储在models中）
    """
    from zml import Seepage
    if path is None:
        path = os.getcwd()
    change_fmt(path=path, ext='.seepage', keywords=['.txt', 'models'], keep_file=False, create_data=Seepage)
