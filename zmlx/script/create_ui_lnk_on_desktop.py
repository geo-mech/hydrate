"""
在桌面上创建界面启动的快捷方式
"""
import sys
from os.path import dirname, abspath

this_dir: str = abspath(__file__)
sys.path.append(dirname(dirname(dirname(this_dir))))

if __name__ == '__main__':
    from zmlx.alg.sys import create_ui_lnk_on_desktop
    create_ui_lnk_on_desktop()
