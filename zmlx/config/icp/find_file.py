import os


def find_by_day(folder, day):
    """
    从文件夹中找到给定day的文件.
    """
    if not os.path.isdir(folder):
        return

    # 遍历
    name_nearest = None
    dist_nearest = 1.0e100
    for name in os.listdir(folder):
        value = float(name[0: len('00000000000274_96107')].replace('_', '.'))
        if abs(value - day) < dist_nearest:
            dist_nearest = abs(value - day)
            name_nearest = name

    # 返回
    if name_nearest is not None:
        return os.path.join(folder, name_nearest)


def find_by_year(folder, year):
    """
    从文件夹中找到给定year的文件.
    """
    return find_by_day(folder, year * 365)
