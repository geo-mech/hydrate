import os
import subprocess
import sys


def pip_install(package_name, name=None, show_exists=True):
    """使用pip安装指定的Python包。

    如果提供了name参数，会先检查该模块是否已存在，只有在模块不存在时才会安装package_name。

    Args:
        show_exists: 在包已经存在的时候，是否显示提示信息。
        package_name (str): 要安装的Python包名称。
        name (str, optional): 要检查的模块名称。如果为None，则直接安装package_name。

    Returns:
        None
    """
    try:
        if name is not None:
            from importlib.util import find_spec
            if find_spec(name):
                if show_exists:
                    print(f"安装包 {package_name} 已经存在!")
                return
        subprocess.check_call([f'{os.path.abspath(sys.executable)}',
                               '-m', 'pip', 'install',
                               package_name])
    except subprocess.CalledProcessError as e:
        print(f"安装包 {package_name} 失败: {e}")


if __name__ == '__main__':
    pip_install('numpy')
