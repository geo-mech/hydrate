import math
import os
import time
import timeit


def sample_delete(folder, ratio_keep=None, count_keep=None):
    from zmlx.ui import gui
    gui.command()
    if ratio_keep is None and count_keep is None:
        return
    files = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            sample_delete(folder=path, ratio_keep=ratio_keep,
                          count_keep=count_keep)
            continue
        if not os.path.isfile(path):
            continue
        if not os.path.splitext(name)[0].isdigit():
            continue
        else:
            files.append(path)
    if len(files) < 10:
        return
    if ratio_keep is None:
        ratio_keep = 1
    else:
        assert 0 < ratio_keep <= 1
    if count_keep is not None:
        assert count_keep > 0
        ratio_keep = min(ratio_keep, count_keep / len(files))
    n_del = math.floor(len(files) * (1 - ratio_keep))
    if n_del > 5:
        count = 0
        for i in range(n_del):
            assert n_del > 0
            idx = round(i * len(files) / n_del)
            if idx < len(files):
                try:
                    path = files[idx]
                    if os.path.isfile(path):
                        os.remove(files[idx])
                        count += 1
                except:
                    pass
        print(f'Succeed delete {count} Files in Folder {folder}')


def get_new_files(folder, mt=0):
    """
    在给定的文件夹内，查找修改时间比给定的时间更晚的所有晚间。其中当前的时间由time.time()给定
    """
    if not os.path.isdir(folder):
        return []
    files = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            files.extend(get_new_files(folder=path, mt=mt))
            continue
        if os.path.isfile(path):
            if os.path.getmtime(path) >= mt:
                files.append(path)
            continue
    return files


def monitor_files(folder, func, ratio=0.1):
    """
    持续监控一个文件夹，并且当检测到新文件的时候执行给定的函数
    """
    from zmlx.ui import gui
    if not os.path.isdir(folder):
        return
    if func is None:
        return

    idle_t = 0
    busy_t = 0
    t1 = time.time()
    while True:
        gui.break_point()
        if busy_t > idle_t * ratio:
            t_beg = timeit.default_timer()
            time.sleep(0.1)
            idle_t += (timeit.default_timer() - t_beg)
            continue
        else:
            t_beg = timeit.default_timer()
            files = get_new_files(folder, t1)
            t1 = time.time()
            time.sleep(0.1)
            if len(files) > 0:
                func(files)
            busy_t += (timeit.default_timer() - t_beg)


def get_desktop():
    """
    返回本机Desktop文件夹的路径
    """
    return os.path.join(os.path.expanduser("~"), 'Desktop')


if __name__ == '__main__':
    print(get_desktop())
