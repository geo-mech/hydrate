import os


def get_desktop_path(*args):
    # 获取用户主目录
    home_dir = os.path.expanduser("~")
    # 根据不同系统生成可能的桌面路径
    possible_desktop_names = ["Desktop", "桌面"]  # 兼容中英文系统
    for name in possible_desktop_names:
        desktop_path = os.path.join(home_dir, name)
        if os.path.exists(desktop_path):
            return os.path.join(desktop_path, *args)
    # 如果未找到，尝试通过注册表获取（仅Windows）
    if os.name == "nt":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
            return os.path.join(desktop_path, *args)
        except ImportError:
            pass
    raise FileNotFoundError("无法找到桌面路径")


if __name__ == '__main__':
    print(get_desktop_path('x', 'y'))
