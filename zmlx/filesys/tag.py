import datetime
import os
from zmlx.filesys.make_parent import make_parent


def time_string():
    """
    生成一个时间字符串 (类似于 20201021T183800 这样的格式)
    """
    return datetime.datetime.now().strftime("%Y%m%dT%H%M%S")


def is_time_string(s):
    """
    check if the given string is a time string such as 20201021T183800.
    """
    if len(s) != 15:
        return False
    else:
        return s[0: 8].isdigit() and s[8] == 'T' and s[9: 15].isdigit()


def has_tag(folder=None):
    """
    Check if a file like 20201021T183800 exists
    """
    if folder is None:
        names = os.listdir(os.getcwd())
    else:
        if os.path.isdir(folder):
            names = os.listdir(folder)
        else:
            names = []
    for name in names:
        if is_time_string(name):
            return True
    return False


def print_tag(folder=None):
    """
    Print a file, the file name is similar to 20201021T183800, this file can be used as a label for the data,
    and then search the file to locate the data
    """
    if has_tag(folder=folder):
        return
    if folder is None:
        path = time_string()
    else:
        path = os.path.join(folder, time_string())
    with open(make_parent(path), 'w') as file:
        file.write("data_tag\n")
        file.flush()
