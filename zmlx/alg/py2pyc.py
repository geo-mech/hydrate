import os
import py_compile


def py2pyc(input_dir, del_py=False):
    """
    将py文件编译成为pyc. 注意，这是一个危险的操作.
    """
    if os.path.isfile(input_dir):
        py_file = input_dir
        try:
            # 获取 .py 文件的目录和文件名
            file_dir = os.path.dirname(py_file)
            file_name = os.path.basename(py_file)
            # 生成 .pyc 文件的路径
            pyc_file = os.path.join(file_dir, file_name + 'c')
            # 编译 .py 文件到 .pyc 文件
            py_compile.compile(py_file, cfile=pyc_file)
            if del_py:
                try:
                    os.remove(py_file)
                except:
                    pass
            print(f"Compiled {py_file} to {pyc_file}")
        except Exception as e:
            print(f"Failed to compile {py_file}: {e}")

    if os.path.isdir(input_dir):
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.py'):
                    py_file = os.path.join(root, file)
                    py2pyc(py_file, del_py=del_py)

