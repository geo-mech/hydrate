import sys


def in_windows() -> bool:
    """
    判断当前是否处于Windows系统的运行环境
    Returns:
        bool: True表示是Windows系统，False表示不是
    """
    return sys.platform.startswith('win')


def in_linux() -> bool:
    """
    判断当前是否处于Linux系统的运行环境
    Returns:
        bool: True表示是Linux系统，False表示不是
    """
    return sys.platform.startswith('linux')


def in_macos() -> bool:
    """
    判断当前是否处于Mac系统
    Returns:
        bool: True表示是Mac系统，False表示不是
    """
    return sys.platform == 'darwin'
