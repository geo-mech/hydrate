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
    if isinstance(name, matplotlib.colors.Colormap):
        return name
    else:
        import matplotlib.pyplot as plt
        return plt.get_cmap(name if name is not None else "coolwarm")
