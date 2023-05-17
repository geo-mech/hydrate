import os
import random
import string

import numpy as np

from zml import gui


def save_npy(folder, size=0):
    assert os.path.isdir(folder)
    while True:
        gui.command()
        path = os.path.join(folder, ''.join(random.sample(string.ascii_letters, 20)) + '.npy')
        if os.path.exists(path):
            continue
        try:
            print(f'Writing File {path} ... ', end='', flush=True)
            data = np.random.rand(1024 * 1024, 100)
            np.save(path, data)
            assert os.path.isfile(path)
            size += os.path.getsize(path)
        except:
            print('Failed')
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except:
                pass
            break
        else:
            print(f'Succeed. Size = +{size / 1024 ** 3} Gb')
    return size


def del_npy(folder, size=0):
    assert os.path.isdir(folder)
    for name in os.listdir(folder):
        gui.command()
        if os.path.splitext(name)[-1] != '.npy':
            continue
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            if random.random() < 0.2:
                try:
                    print(f'Deleting File {path} ... ', end='', flush=True)
                    size += os.path.getsize(path)
                    os.remove(path)
                except:
                    print('Failed')
                    break
                else:
                    print(f'Succeed. Size = -{size / 1024 ** 3} Gb')
    return size


if gui.question('将填充文件,继续?'):
    size1 = 0
    size2 = 0
    while True:
        size1 = save_npy(os.getcwd(), size1)
        size2 = del_npy(os.getcwd(), size2)
