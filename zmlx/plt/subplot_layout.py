from typing import Optional


def calculate_subplot_layout(
        num_plots: int, subplot_aspect_ratio: Optional[float] = None, canvas_aspect_ratio: Optional[float] = None,
        fig=None):
    """
    计算最优的子图布局（行数和列数）

    Args:
        num_plots : int
            需要绘制的子图数量
        subplot_aspect_ratio : float, 默认=1.0
            单个子图的宽高比（宽度/高度）
        canvas_aspect_ratio : float, 默认=1.0
            整个画布的宽高比（宽度/高度）
        fig : matplotlib.figure.Figure, 默认=None
            用于获取画布宽高比的Figure对象
    Returns:
        tuple : (n_rows, n_cols)
            最优的行数和列数
    """
    if canvas_aspect_ratio is None:
        if fig is not None:
            canvas_aspect_ratio = fig.get_figwidth() / fig.get_figheight()
        else:
            canvas_aspect_ratio = 1.0

    if subplot_aspect_ratio is None:
        subplot_aspect_ratio = canvas_aspect_ratio

    # 画布的宽度和高度
    canvas_w = canvas_aspect_ratio
    canvas_h = 1.0

    if num_plots <= 0:
        return 1, 1

    if num_plots == 1:
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


def test():
    import matplotlib.pyplot as plt

    num_plots = 12
    n_rows, n_cols = calculate_subplot_layout(num_plots, subplot_aspect_ratio=1, canvas_aspect_ratio=1.5)
    print(f"对于{num_plots}个子图，推荐布局: {n_rows}行 × {n_cols}列")

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6, 4))

    # 将axes转换为一维数组便于遍历
    if n_rows * n_cols > 1:
        axes_flat = axes.flatten()
    else:
        axes_flat = [axes]

    # 绘制示例图形
    for i, ax in enumerate(axes_flat):
        if i < num_plots:
            ax.plot([0, 1, 2], [0, 1, 0.5])
            ax.set_title(f'Subplot {i + 1}')
        else:
            ax.axis('off')  # 隐藏多余的子图

    plt.tight_layout()
    plt.show()


# 使用示例
if __name__ == "__main__":
    test()
