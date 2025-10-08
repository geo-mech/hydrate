"""
安装模块所需要必要的包。如果出现安装比较缓慢的情况，可以首先运行 write_pip_config来使用清华大学的镜像源
"""
import sys
from os.path import dirname, abspath

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))

if __name__ == '__main__':
    from zmlx.alg.sys import install_dep

    install_dep()
