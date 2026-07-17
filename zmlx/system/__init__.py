"""
系统模块，提供zmlx中配置的基础服务。不可以依赖zmlx中的其他任何内容。其实，本来exts中的内容，对于
zmlx来说是基础的，但是，exts目前有些庞大了。如果exts中有的内容，需要被其他部分使用，那么，可以
放在system里面。

since 2026-6-29
"""

from zmlx.system._app_data import app_data, get_user_data_dir
from zmlx.system._deprecated import deprecated
from zmlx.system._fsys import make_parent, make_dirs
from zmlx.system._hash import get_hash
from zmlx.system._heatless import is_headless
from zmlx.system._log import log
from zmlx.system._mail import sendmail
from zmlx.system._once import execute_once, first_execute
from zmlx.system._os import in_linux, in_windows, in_macos
from zmlx.system._self_path import SelfPath
from zmlx.system._text import read_text, write_text
from zmlx.system._warn import warn
