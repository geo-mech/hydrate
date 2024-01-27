import os

from zmlx.alg.fsize2str import fsize2str

__all__ = ['dirname', 'basename', 'abspath', 'exists', 'isdir', 'isfile', 'getsize', 'getatime', 'getmtime', 'getctime',
           'samefile', 'join', 'getsize_str']


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
join = get_protected(os.path.join, None)


def getsize_str(filename):
    """
    将文件的大小，显示为字符串
    """
    return fsize2str(getsize(filename))
