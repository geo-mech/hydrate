import os
from zmlx.filesys.make_parent import make_parent
from zmlx.filesys.join_paths import join_paths

tag = 'icp_xz.txt'


def find_root():
    """
    搜索找到数据的主目录. 定义了文件icp_xz.txt的目录.
    """
    folder = os.path.dirname(os.path.realpath(__file__))

    depth = 0
    while os.path.exists(folder) and depth < 3:
        f_name = os.path.join(folder, tag)
        if os.path.exists(f_name):
            return folder
        else:
            try:
                parent = os.path.dirname(folder)
                if os.path.samefile(parent, folder):
                    break
                else:
                    folder = parent
                    depth += 1
            except:
                return


def opath(*args):
    """
    返回输出的目录
    """
    return make_parent(join_paths(find_root(), *args))


if __name__ == '__main__':
    print(opath())
