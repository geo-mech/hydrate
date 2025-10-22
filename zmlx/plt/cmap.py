try:
    import matplotlib
    import matplotlib.pyplot as plt
except ImportError:
    matplotlib = None
    plt = None


def get_color(cmap, lr, rr, val):
    """
    根据给定的颜色映射和数值范围，返回数值对应的颜色

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        Matplotlib 颜色映射对象，必须包含至少2种颜色 (cmap.N >= 2)
    lr : float
        数值范围左边界 (left range)，通常为最小值
    rr : float
        数值范围右边界 (right range)，通常为最大值
    val : float
        需要映射颜色的目标数值

    Returns
    -------
    tuple
        RGBA 颜色元组，格式为 (R, G, B, A)，每个分量取值范围 [0, 1]

    Raises
    ------
    AssertionError
        当颜色映射颜色数不足或数值范围无效时触发

    Notes
    -----
    1. 当 lr >= rr 时视为无效范围，返回颜色映射中间位置的颜色
    2. 数值超出范围时返回端点颜色
    3. 使用线性插值计算颜色位置，分母添加极小值防止除零错误
    """
    assert isinstance(cmap, matplotlib.colors.Colormap)
    # 确保颜色映射至少包含2种颜色（否则无法进行线性插值）
    assert cmap.N >= 2, "Colormap must contain at least 2 colors"

    # 处理无效数值范围（左边界 >= 右边界）
    if lr >= rr:
        # 返回中间颜色（例如：256色映射返回第128号颜色）
        return cmap(int(cmap.N / 2))

    # 验证有效数值范围（左边界 < 右边界）
    assert lr < rr, "Invalid value range: left boundary must be smaller than right boundary"

    # 处理数值超出下限的情况
    if val <= lr:
        return cmap(0)  # 返回颜色映射的第一个颜色

    # 处理数值超出上限的情况
    if val >= rr:
        return cmap(cmap.N - 1)  # 返回颜色映射的最后一个颜色

    # 计算颜色索引（核心逻辑）
    numerator = val - lr  # 分子：当前值相对于左边界的偏移量
    denominator = rr - lr  # 分母：数值范围宽度
    safe_denominator = max(denominator, 1.0e-100)  # 防止除零错误（处理极小范围）

    # 线性映射公式：
    # (当前值 - 最小值) / (最大值 - 最小值) * 颜色总数
    raw_index = (numerator / safe_denominator) * cmap.N

    # 限制索引在有效范围内 [0, cmap.N-1]
    # 使用整数转换实现离散化颜色选择
    i = max(0, min(cmap.N - 1, int(raw_index)))

    return cmap(i)


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
    if isinstance(name, matplotlib.colors.Colormap):
        return name

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



def resample(cmap, lutsize):
    assert isinstance(cmap, matplotlib.colors.Colormap)
    return cmap.resampled(lutsize)


def test_1():
    cmap = get_cm()
    print(get_color(cmap, 0, 1, 0.5))
    print(get_color(cmap, 0, 1, 0.0))
    print(get_color(cmap, 0, 1, 1.0))
    print(get_color(cmap, 0, 1, -1.0))

    # (np.float64(0.8674276350862745), np.float64(0.864376599772549), np.float64(0.8626024620196079), np.float64(1.0))
    # (np.float64(0.2298057), np.float64(0.298717966), np.float64(0.753683153), np.float64(1.0))
    # (np.float64(0.705673158), np.float64(0.01555616), np.float64(0.150232812), np.float64(1.0))
    # (np.float64(0.2298057), np.float64(0.298717966), np.float64(0.753683153), np.float64(1.0))


if __name__ == '__main__':
    test_1()
