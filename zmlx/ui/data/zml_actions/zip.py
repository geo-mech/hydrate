# ** text = '压缩'
# ** menu = "文件"

import os
import zipfile

from zml import gui

dataname = 'files.zip'


def is_time_string(s):
    """
    check if the given string is a time string such as 20201021T183800.
    """
    if len(s) != 15:
        return False
    else:
        return s[0: 8].isdigit() and s[8] == 'T' and s[9: 15].isdigit()


def zip(folder, this_only=False):
    gui.break_point()
    if not os.path.isdir(folder):
        return
    if this_only:
        if os.path.isfile(os.path.join(folder, dataname)):
            return
        all = []
        fs_all = 0
        try:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if name == dataname or is_time_string(name):
                    continue
                if not os.path.isfile(path):
                    continue
                # if os.path.samefile(__file__, path):
                #     continue
                fs = os.path.getsize(path) / 1024.0 ** 2
                if fs > 200:
                    continue
                else:
                    all.append((name, path))
                    fs_all += fs
        except Exception as e:
            print(f'Error: {e}')
            all = []
        if len(all) < 2:
            return
        if fs_all > 10000 or fs_all / len(all) > 50:
            return
        try:
            print(f'Zip {folder} ... ', end='', flush=True)
            z = zipfile.ZipFile(os.path.join(folder, dataname), 'w', zipfile.ZIP_DEFLATED)
            for name, path in all:
                z.write(filename=path, arcname=name)
            z.close()
            for name, path in all:
                os.remove(path)
        except:
            print('Failed')
        else:
            print('Succeed')
    else:
        try:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if os.path.isdir(path):
                    zip(path, this_only=False)
            zip(folder, this_only=True)
        except KeyboardInterrupt:
            return
        except:
            pass


if gui.question('This is a dangerous operation, and a large number of '
                'files will be changed in the working path.  To continue? '):
    zip(os.getcwd())
