"""
在桌面上创建界面启动的快捷方式
"""
import sys
from os.path import dirname, abspath

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))

from zmlx.alg.sys import create_ui_lnk_on_desktop

if __name__ == '__main__':
    create_ui_lnk_on_desktop()
