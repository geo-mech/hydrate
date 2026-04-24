"""
安全地打开zmlx的GUI界面。不加载任何配置文件。
"""

import sys
from os.path import dirname, abspath

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))

if __name__ == "__main__":
    from zmlx import open_gui_without_setup

    open_gui_without_setup(sys.argv)
