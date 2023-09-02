import time
from zmlx.filesys.path import getatime, getmtime, isfile, getsize_str


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
