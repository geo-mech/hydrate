import os


def get_last_file(folder):
    """
    返回给定文件夹中的最后一个文件（按照文件名，利用字符串默认的对比，从小到大排序）
    """
    if not os.path.isdir(folder):
        return
    files = os.listdir(folder)
    if len(files) == 0:
        return
    else:
        return os.path.join(folder, max(files))
