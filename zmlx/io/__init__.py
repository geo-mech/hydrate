"""IO 工具（文件读写、JSON、路径管理）.

Modified by Claude, 2026-08-12
"""

from zmlx.io.base import append_file, load_txt
from zmlx.io.base import load_txt as loadtxt
from zmlx.io.path import get_path as opath
from zmlx.io.path import set_path
from zmlx.io.python import read_py, write_py

if __name__ == "__main__":
    print(opath())
