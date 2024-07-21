import os


def in_directory(file_name, directory):
    """
    判断给定的文件是否位于给定的路径或者其子目录下.
        by GPT 3.5. @2024-7-22
    """
    # 获取文件的绝对路径
    file_path = os.path.abspath(file_name)

    # 获取目录的绝对路径
    directory_path = os.path.abspath(directory)

    return file_path.startswith(directory_path)


def test():
    file_name = r'C:\Users\zhaob\OneDrive\MyProjects\ZNetwork\projects\zml\zmlx\filesys\in_directory.py'
    directory = r'C:\Users\zhaob\OneDrive\MyProjects\ZNetwork\projects\zml'

    if in_directory(file_name, directory):
        print(f"{file_name} 在 {directory} 下或其子目录中")
    else:
        print(f"{file_name} 不在 {directory} 下或其子目录中")


if __name__ == '__main__':
    test()
