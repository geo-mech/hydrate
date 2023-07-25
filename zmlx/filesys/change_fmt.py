from zmlx.filesys.list_files import list_files
import os
import sys


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


def proc(argv):
    """
    处理预定义的一些命令
    """
    if len(argv) <= 1:
        return
    key = argv[1]
    print(f'process data format change. key = {key}')

    if key == 'disc2txt':
        from zml import Disc3Vec
        change_fmt(convert=None, ext='.txt',
                   path=os.getcwd(),
                   keywords=['discs', '.dat'],
                   keep_file=False, create_data=Disc3Vec)
        return

    if key == 'seep2txt':
        from zml import Seepage
        change_fmt(convert=None, ext='.txt',
                   path=os.getcwd(),
                   keywords=['seepage', '.dat'],
                   keep_file=False, create_data=Seepage)
        return

    if key == 'txt2disc':
        from zml import Disc3Vec
        change_fmt(convert=None, ext='.dat',
                   path=os.getcwd(),
                   keywords=['discs', '.txt'],
                   keep_file=False, create_data=Disc3Vec)
        return

    if key == 'txt2seep':
        from zml import Seepage
        change_fmt(convert=None, ext='.dat',
                   path=os.getcwd(),
                   keywords=['seepage', '.txt'],
                   keep_file=False, create_data=Seepage)
        return

    if key == 'to_bin':
        from zml import Disc3Vec, Seepage

        change_fmt(convert=None, ext='.dat',
                   path=os.getcwd(),
                   keywords=['discs', '.txt'],
                   keep_file=False, create_data=Disc3Vec)

        change_fmt(convert=None, ext='.dat',
                   path=os.getcwd(),
                   keywords=['seepage', '.txt'],
                   keep_file=False, create_data=Seepage)
        return

    if key == 'to_txt':
        from zml import Disc3Vec, Seepage

        change_fmt(convert=None, ext='.txt',
                   path=os.getcwd(),
                   keywords=['discs', '.dat'],
                   keep_file=False, create_data=Disc3Vec)

        change_fmt(convert=None, ext='.txt',
                   path=os.getcwd(),
                   keywords=['seepage', '.dat'],
                   keep_file=False, create_data=Seepage)
        return


if __name__ == '__main__':
    proc(sys.argv)
