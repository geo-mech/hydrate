import os
import zipfile

from zml import gui

dataname = 'files.zip'


def unzip(folder, this_only=False):
    gui.break_point()
    if not os.path.isdir(folder):
        return
    if this_only:
        file = os.path.join(folder, dataname)
        if os.path.isfile(file):
            try:
                print(f'Unzip {file} ... ', end='', flush=True)
                z = zipfile.ZipFile(file, 'r')
                z.extractall(folder)
                z.close()
                os.remove(file)
            except:
                print('Failed')
            else:
                print('Succeed')
        all = []
        try:
            for name in os.listdir(folder):
                parts = os.path.splitext(name)
                ext = parts[-1]
                if ext != '.zip':
                    continue
                path = os.path.join(folder, name)
                if not os.path.isfile(path):
                    continue
                log = os.path.join(folder, parts[0] + '.log')
                if not os.path.isfile(log):
                    continue
                else:
                    all.append((parts[0], log, path))
        except:
            all = []

        for subdir, log, path in all:
            try:
                print(f'Unzip {path} ... ', end='', flush=True)
                z = zipfile.ZipFile(path, 'r')
                z.extractall(os.path.join(folder, subdir))
                z.close()
                os.remove(path)
                os.remove(log)
            except:
                print('Failed')
            else:
                print('Succeed')
    else:
        try:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if os.path.isdir(path):
                    unzip(path, this_only=False)
            unzip(folder, this_only=True)
        except KeyboardInterrupt:
            return
        except:
            pass


if gui.question('This is a dangerous operation, and a large number of '
                'files will be changed in the working path.  To continue? '):
    unzip(os.getcwd())
