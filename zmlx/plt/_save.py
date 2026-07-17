"""
matplotlib 图片保存路径工具。
"""

import os


def set_plt_save_path(path):
    """设置matplotlib保存图片的路径。

    Args:
        path (str): 保存图片的完整路径
    """
    from zmlx.system import app_data

    app_data.set("matplotlib_autosave", path)
    try:
        from zmlx.system import make_dirs
        make_dirs(path)
    except:
        pass


def get_plt_save_path(*subdirs):
    """返回matplotlib保存图片的路径。

    接受可选的字符串参数作为子目录。每个字符串会被检查是否适合作为路径组件
    （不包含非法字符、非空、非 "." 或 ".."），不适合的会使用 get_hash 处理。

    Args:
        *subdirs: 可选的子目录名称

    Returns:
        str: 保存图片的完整路径
    """
    from zmlx.system import app_data, get_hash
    import re

    from zmlx.alg import join_paths

    # 非法路径字符（Windows + 通用控制字符）
    _INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

    def _safe_name(s):
        """如果字符串不适合作为路径组件，返回其 hash 值"""
        if (
                not isinstance(s, str)
                or not s
                or len(s) > 200
                or _INVALID_CHARS.search(s)
                or s in (".", "..")
        ):
            raw = s if isinstance(s, str) else repr(s)
            return get_hash(raw)
        return s.strip()

    matplotlib_autosave = app_data.get("matplotlib_autosave")
    if not isinstance(matplotlib_autosave, str):
        matplotlib_autosave = os.environ.get("ZMLX_PLT_SAVE_PATH")
    if isinstance(matplotlib_autosave, str):
        base = matplotlib_autosave
    else:  # 使用默认路径
        import datetime
        from zmlx.io import opath

        now = datetime.datetime.now()
        time_str = now.strftime("%Y-%m-%d-%H-%M-%S-") + f"{now.microsecond:06d}"
        base = opath("matplotlib", time_str)  # 确保每次启动不一样，避免覆盖
        if base is None:
            base = join_paths(os.getcwd(), time_str)
        app_data.set("matplotlib_autosave", base)
        print(f"matplotlib_autosave: {base}")

    components = [base]
    for sub in subdirs:
        components.append(_safe_name(sub))

    res = join_paths(*components)
    try:
        from zmlx.system import make_parent
        make_parent(res)
    except:
        pass
    return res


def test():
    """测试 get_plt_save_path：验证正常路径和非法字符处理"""
    # 无参数
    p = get_plt_save_path()
    assert isinstance(p, str) and len(p) > 0, f"path should be non-empty string: {p}"
    print(f"OK: {p}")

    # 正常子目录
    p = get_plt_save_path("hydrate", "test")
    assert "hydrate" in p and "test" in p, f"subdirs should be in path: {p}"
    print(f"OK: {p}")

    # 非法字符子目录 → hash
    p = get_plt_save_path("a/b?c")
    assert "a/b?c" not in p, f"invalid chars should be hashed: {p}"
    print(f"OK: {p}")

    # 空字符串 → hash
    p = get_plt_save_path("")
    print(f"OK: {p}")

    print("All tests passed.")


if __name__ == "__main__":
    test()
