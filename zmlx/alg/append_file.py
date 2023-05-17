
from zml import make_parent


def append_file(filename, text):
    """
    在给定文件的末尾附加文本
    :param filename: 文件名（当为None的时候则不执行操作）
    :param text: 要附加的文本或者其它可以通过file来write的数据
    :return: None
    """
    try:
        if filename is not None:
            with open(make_parent(filename), 'a') as file:
                file.write(text)
    except:
        pass
