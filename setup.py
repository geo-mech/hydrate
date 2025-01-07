import os
import sys

from setuptools import setup, find_packages
from setuptools.command.install import install


class Command(install):
    def run(self):
        # 运行安装过程的父类方法
        install.run(self)

        # 获取用户的桌面路径
        if sys.platform == "win32":
            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            # 创建文件路径
            file_path = os.path.join(desktop, "IggHydrate.bat")
            # 在桌面上创建文件
            with open(file_path, "w") as f:
                f.write(f"{sys.executable} -m zml_ui")


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
    version='1.3.12',  # 包版本
    description='IggHydrate',  # 描述
    author='Zhaobin Zhang',  # 作者名称
    author_email='zhangzhaobin@mail.iggcas.ac.cn',  # 作者邮箱
    packages=find_packages(),  # 查找所有的包目录
    package_data=package_data,  # 包含额外文件
    include_package_data=True,  # 确保所有指定的文件被包括
    install_requires=install_requires,
    cmdclass={'install': Command},
)
