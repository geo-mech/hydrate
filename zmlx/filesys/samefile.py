import os


def samefile(x, y):
    try:
        return os.path.samefile(x, y)
    except:
        return False
