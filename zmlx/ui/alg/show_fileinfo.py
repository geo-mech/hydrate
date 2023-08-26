import os
import time


def show_fileinfo(filepath):
    try:
        if os.path.isfile(filepath):
            print(f'File   Path: {filepath}')
            print(f'File   Size: {os.path.getsize(filepath) / (1024 * 1024)} Mb')
            print(f'Access Time: {time.ctime(os.path.getatime(filepath))}')
            print(f'Modify Time: {time.ctime(os.path.getmtime(filepath))}')
            print('\n\n')
    except:
        pass
