"""
定义具体的应用场景（scenario）：具体需要解决的问题。基于zmlx中的其它模块，实现最接近应用的功能配置。
"""

from zmlx.exts import SelfPath

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
