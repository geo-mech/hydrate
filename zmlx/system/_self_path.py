import os

from zmlx.system._fsys import make_parent


class SelfPath:
    """
    返回基于当前文件的路径
    """

    def __init__(self, this_file):
        self.this_dir = os.path.dirname(os.path.abspath(this_file))

    def __call__(self, *args, mkdir: bool = False) -> str:
        res = os.path.join(self.this_dir, *args)
        if isinstance(res, str):
            if mkdir:
                make_parent(res)
            return res
        else:
            return ""
