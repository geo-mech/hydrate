import os
import sys

from setuptools import setup, find_packages


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
    if sys.version_info >= (3, 8):  # 尽可能使用PyQt6
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
    version='1.4.7',  # 包版本
    description='IggHydrate',  # 描述
    author='Zhaobin Zhang',  # 作者名称
    author_email='zhangzhaobin@mail.iggcas.ac.cn',  # 作者邮箱
    packages=find_packages(),  # 查找所有的包目录
    package_data=package_data,  # 包含额外文件
    include_package_data=True,  # 确保所有指定的文件被包括
    install_requires=install_requires
)
