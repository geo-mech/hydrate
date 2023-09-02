import os


def has_permission(folder):
    """
    是否有权限读取文件夹
    """
    try:
        os.listdir(folder)
        return True
    except:
        return False
