from pathlib import Path

import win32com.client  # pip_install('pypiwin32')


def create_shortcut(target: str, path: str,
                    arguments: str = "",
                    working_dir: str = None,
                    icon_path: str = None,
                    description: str = "Python Shortcut") -> None:
    """
    在指定路径创建指向目标的Windows快捷方式

    参数:
        target (str): 目标文件/程序的完整路径
        path (str): 快捷方式保存路径（需包含.lnk扩展名）
        arguments (str): 启动参数（可选）
        working_dir (str): 工作目录（默认目标所在目录）
        icon_path (str): 图标文件路径（可选）
        description (str): 快捷方式描述（可选）
    """
    try:
        # 验证目标路径是否存在
        if not Path(target).exists():
            raise FileNotFoundError(f"目标文件不存在: {target}")

        # 确保保存路径包含.lnk扩展名
        path = str(Path(path).with_suffix('.lnk'))

        # 创建父目录（如果不存在）
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # 创建快捷方式对象
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)

        # 设置基本属性
        shortcut.TargetPath = str(Path(target).resolve())
        shortcut.Arguments = arguments
        shortcut.Description = description

        # 设置工作目录（优先使用参数，否则取目标所在目录）
        if working_dir:
            shortcut.WorkingDirectory = str(Path(working_dir).resolve())
        else:
            shortcut.WorkingDirectory = str(Path(target).parent.resolve())

        # 设置自定义图标
        if icon_path and Path(icon_path).exists():
            shortcut.IconLocation = str(Path(icon_path).resolve())

        # 保存快捷方式
        shortcut.save()
        print(f"快捷方式已创建于：{path}")

    except Exception as e:
        raise RuntimeError(f"创建快捷方式失败: {str(e)}") from e
