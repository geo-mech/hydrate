"""
之前测试，在某些运行环境下，pip的默认源比较慢，所以这里提供一个脚本，用于写入pip的配置文件，使用清华大学的镜像源。
"""
import getpass
import os


def write_pip_config():
    # 获取当前用户名
    username = getpass.getuser()

    # 构建配置文件路径
    config_path = rf"C:\Users\{username}\pip\pip.ini"

    # 确保pip目录存在
    pip_dir = os.path.dirname(config_path)
    if not os.path.exists(pip_dir):
        os.makedirs(pip_dir)
        print(f"创建目录: {pip_dir}")

    # 配置内容
    config_content = """[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
"""

    # 写入配置文件
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)

    print(f"配置文件已更新: {config_path}")
    print("已设置清华镜像源为pip的默认源")


if __name__ == '__main__':
    write_pip_config()
