import os
import subprocess
import sys


def pip_install(package_name):
    """
    尝试使用pip来安装一个包. 其中package_name是一个字符串，包含了要安装的包的名称
    """
    try:
        subprocess.check_call([f'{os.path.abspath(sys.executable)}',
                               '-m', 'pip', 'install',
                               package_name])
    except subprocess.CalledProcessError as e:
        print(f"安装包 {package_name} 失败: {e}")


if __name__ == '__main__':
    pip_install('numpy')
