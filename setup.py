import os

from setuptools import setup, find_packages

# 获取当前目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义要包括的额外文件
package_data = {
    '': [os.path.join(current_dir, 'zml.py'),
         os.path.join(current_dir, 'zml.dll'),
         os.path.join(current_dir, 'README.md'),
         os.path.join(current_dir, 'zmlx/*'),
         ],
}

# 使用 setup() 函数定义包的元数据
setup(
    name='IggHydrate',  # 包名称
    version='1.3.9',  # 包版本
    description='IggHydrate',  # 描述
    author='Zhaobin Zhang',  # 作者名称
    author_email='zhangzhaobin@mail.iggcas.ac.cn',  # 作者邮箱
    packages=find_packages(),  # 查找所有的包目录
    package_data=package_data,  # 包含额外文件
    include_package_data=True,  # 确保所有指定的文件被包括
    install_requires=['numpy',
                      'scipy',
                      'matplotlib',
                      'pyqtgraph',
                      'PyQt5'],  # 如果有外部依赖，可以在这里列出
)
