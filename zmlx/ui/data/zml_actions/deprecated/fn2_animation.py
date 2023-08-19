# ** tooltip = '查找当前路径下所有扩展名为.fn2的文件并进行循环绘图显示'
# ** text = 'fn2动画'

import os
import time
import timeit

from zml import gui


def list_files(folder, ext):
    if not os.path.isdir(folder):
        return []
    paths = []
    for name in os.listdir(folder):
        gui.break_point()
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            for subpath in list_files(path, ext):
                paths.append(subpath)
            continue
        if os.path.isfile(path):
            if os.path.splitext(path)[1] == ext:
                paths.append(path)
    return paths


def animation(ext, show, step=1, sleep=0.01):
    assert gui.exists()
    if show is None:
        return
    files = list_files(os.getcwd(), ext)

    t0 = timeit.default_timer()
    if len(files) > 0:
        n = 0
        while True:
            for file in files:
                gui.break_point()
                n += 1
                if n % 100 == 0 and n > 0:
                    elapsed = timeit.default_timer() - t0
                    gui.status(f'正在绘制动画，耗时 = {elapsed}秒/{n}次 = {elapsed / n}秒/次')
                if n % step != 0:
                    continue
                print(os.path.relpath(file))
                show(file)
                time.sleep(sleep)
    else:
        print(f'Warning: {ext} files not found')


animation('.fn2', gui.show_fn2, step=10, sleep=0.01)
