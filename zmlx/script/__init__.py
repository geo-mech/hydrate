"""
直接执行的脚本，用于测试和验证zmlx的功能。不可以在外部导入这些脚本。
"""

from zmlx.exts import SelfPath

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
