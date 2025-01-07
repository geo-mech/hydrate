import os
import sys
import warnings

from setuptools import setup, find_packages


# 检查路径中是否包含中文字符
def check_path_for_chinese(path):
    # 使用正则表达式匹配中文字符
    return any('\u4e00' <= ch <= '\u9fff' for ch in path)


# 获取安装路径（例如 sys.prefix 是 Python 的安装路径）
install_path = sys.prefix  # 或者你可以使用 sys.exec_prefix，具体取决于你的需求

# 如果安装路径包含中文字符，发出警告
if check_path_for_chinese(install_path):
    warnings.warn(f"警告：安装路径包含中文字符，当前路径为：{install_path}。IggHydrate不支持包含中文的路径。", UserWarning)


def pyqt_installed():
    try:
        import PyQt5
        return True
    except:
        pass
    try:
        import PyQt6
        return True
    except:
        return False


install_requires = [
    'numpy',
    'scipy',
    'matplotlib',
    'pyqtgraph',
    'PyOpenGL',
]

if not pyqt_installed():
    if sys.version_info >= (3, 10):  # Python 版本大于 3.11
        install_requires.append('PyQt6')
        install_requires.append('PyQt6-WebEngine')
    else:
        install_requires.append('PyQt5')
        install_requires.append('PyQtWebEngine')

# 获取当前目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义要包括的额外文件
package_data = {
    '': [os.path.join(current_dir, 'zml.py'),
         os.path.join(current_dir, 'zml.dll'),
         os.path.join(current_dir, 'README.md'),
         os.path.join(current_dir, 'zml_ui.pyw'),
         os.path.join(current_dir, 'zmlx/*'),
         ],
}

# 使用 setup() 函数定义包的元数据
setup(
    name='IggHydrate',  # 包名称
    version='1.3.11',  # 包版本
    description='IggHydrate',  # 描述
    author='Zhaobin Zhang',  # 作者名称
    author_email='zhangzhaobin@mail.iggcas.ac.cn',  # 作者邮箱
    packages=find_packages(),  # 查找所有的包目录
    package_data=package_data,  # 包含额外文件
    include_package_data=True,  # 确保所有指定的文件被包括
    install_requires=install_requires,
)
