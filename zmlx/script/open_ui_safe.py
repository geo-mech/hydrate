"""
安全地打开zmlx的GUI界面。不加载任何配置文件。
"""

import sys
from os.path import dirname, abspath

this_dir: str = abspath(__file__)
sys.path.append(dirname(dirname(dirname(this_dir))))

if __name__ == "__main__":
    from zmlx import open_gui_without_setup

    open_gui_without_setup(sys.argv)
