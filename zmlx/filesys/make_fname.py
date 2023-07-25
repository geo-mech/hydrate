import os


def make_fname(time, folder=None, ext=None, unit=None):
    """
    根据给定的时间，生成一个文件名(或者一个文件路径)，用以存储文件;
    如果folder不存在，则此函数会自动创建这个folder
    如果folder为None，则返回None
    """
    if folder is None:
        return
    name = ('%020.5f' % time).replace('.', '_')
    if unit is not None:
        name = name + unit
    if ext is not None:
        name = name + ext
    if len(folder) > 0:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        name = os.path.join(folder, name)
    return name


if __name__ == '__main__':
    print(make_fname(1, '.', '.txt'))
