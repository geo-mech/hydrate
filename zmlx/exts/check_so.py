"""
尝试导入 zml.so 文件
"""
import ctypes
import os

# so 文件路径（推荐用绝对路径）
so_path = os.path.join(os.path.dirname(__file__), "zml.so")

# 加载动态库
dll = ctypes.CDLL(so_path)

dll.get_version.restype = ctypes.c_int
print(dll.get_version())
