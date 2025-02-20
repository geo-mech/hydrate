import os
import py_compile
import shutil
import sys


def py2pyc(ipath: str, opath: str):
    """
    编译py文件(对于非py文件，则简单复制)
    """

    if os.path.isfile(ipath):  # 对于Python文件，执行编译操作;
        assert ipath.endswith('.py') and opath.endswith('.pyc')
        try:
            folder = os.path.dirname(opath)
            if not os.path.isdir(folder):
                os.makedirs(folder, exist_ok=True)
            py_compile.compile(ipath, cfile=opath)
            print(f"Succeed: {ipath} -> {opath}")
        except Exception as e:
            print(f"Failed: {ipath}. {e}")

    elif os.path.isdir(ipath):  # 对于目录，则遍历执行
        for name in os.listdir(ipath):
            path = os.path.join(ipath, name)
            if os.path.isfile(path):  # 对于文件
                if name.endswith('.py'):  # 对于Python文件，则尝试编译
                    py2pyc(ipath=path, opath=os.path.join(opath, name + 'c'))
                else:  # 对于普通的文件，则尝试拷贝
                    try:
                        if not os.path.isdir(opath):
                            os.makedirs(opath, exist_ok=True)
                        if not os.path.samefile(ipath, opath):
                            shutil.copy(path, os.path.join(opath, name))
                            print(f"Succeed: {path} -> {os.path.join(opath, name)}")
                    except Exception as e:
                        print(f"Failed: {path}. {e}")
            elif os.path.isdir(path):  # 对于路径，则递归执行
                if name != '__pycache__' and name != '.git':  # 忽略缓存目录
                    py2pyc(ipath=path, opath=os.path.join(opath, name))
                else:
                    print(f'Ignore: {path}')


if __name__ == '__main__':
    if len(sys.argv) == 3:
        py2pyc(ipath=sys.argv[1], opath=sys.argv[2])
