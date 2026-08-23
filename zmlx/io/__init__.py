"""IO 工具（文件读写、JSON、路径管理）.

Modified by Claude, 2026-08-12
"""
from zmlx.io.base import append_file
from zmlx.io.base import load_txt
from zmlx.io.base import load_txt as loadtxt
from zmlx.io.path import get_path as opath, set_path

if __name__ == '__main__':
    print(opath())
