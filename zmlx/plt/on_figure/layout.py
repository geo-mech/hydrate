from typing import Optional


def calc_best_layout(
        fig, num_plots: int, subplot_aspect_ratio: Optional[float] = None):
    """
    计算最优的子图布局（行数n_rows和列数n_cols）

    Args:
        fig : matplotlib.figure.Figure,
            用于获取画布宽高比的Figure对象
        num_plots : int
            需要绘制的子图数量
        subplot_aspect_ratio : float, 默认=1.0
            单个子图的宽高比（宽度/高度）
    Returns:
        tuple : (n_rows, n_cols)
            最优的行数和列数
    """
    try:
        canvas_aspect_ratio = fig.get_figwidth() / fig.get_figheight()
    except:
        canvas_aspect_ratio = 1.0

    if subplot_aspect_ratio is None:
        subplot_aspect_ratio = 1.0

    # 画布的宽度和高度
    canvas_w = canvas_aspect_ratio
    canvas_h = 1.0

    if num_plots <= 1:
        return 1, 1

    # 初始化最佳布局
    best_layout = None
    best_area = 0.0

    # 遍历所有可能的行列组合
    for n_cols in range(1, num_plots + 1):
        for n_rows in range(1, num_plots + 1):
            if n_rows * n_cols >= num_plots:
                # 子图区域宽度和高度
                subplot_w = canvas_w / n_cols
                subplot_h = canvas_h / n_rows

                # 可以显示的面积
                if subplot_w / subplot_h < subplot_aspect_ratio:
                    area = subplot_w * subplot_w / subplot_aspect_ratio
                else:
                    area = subplot_h * subplot_h * subplot_aspect_ratio

                if area > best_area:
                    best_area = area
                    best_layout = (n_rows, n_cols)

    return best_layout
