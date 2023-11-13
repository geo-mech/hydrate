import math
import os

from zmlx.ui.GuiBuffer import gui


def sample_delete(folder, ratio_keep=None, count_keep=None):
    gui.command()
    if ratio_keep is None and count_keep is None:
        return
    files = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            sample_delete(folder=path, ratio_keep=ratio_keep, count_keep=count_keep)
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


if __name__ == '__main__':
    sample_delete(os.getcwd(), count_keep=100)
