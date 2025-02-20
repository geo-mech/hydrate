def get_cm(name=None):
    """
    根据 Matplotlib 版本自动选择最佳方法获取 Colormap
    该实现兼容 Matplotlib ≥1.4 的所有版本，并自动选择各版本推荐的最佳实践方法。

    参数:
        name (str): Colormap 名称（如 "coolwarm"）

    返回:
        matplotlib.colors.Colormap: 对应的 Colormap 对象

    异常:
        ValueError: 如果名称对应的 Colormap 不存在
    """
    import matplotlib
    import matplotlib.pyplot as plt

    parts = []
    version_str = matplotlib.__version__
    for part in version_str.split('.'):
        cleaned = []
        for char in part:
            if char.isdigit():
                cleaned.append(char)
            else:
                break  # 遇到非数字字符停止解析该部分
        if cleaned:
            parts.append(int(''.join(cleaned)))
        else:
            break  # 没有有效数字部分时停止解析
    version_tuple = tuple(parts)

    if name is None:
        name = 'coolwarm'

    # 版本判断逻辑
    if version_tuple >= (3, 5):
        return matplotlib.colormaps[name]  # 3.5+ 推荐方式
    else:
        return plt.get_cmap(name)  # 旧版本兼容方式
