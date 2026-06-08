import zmlx.alg.sys as warnings
from zmlx.plt.on_figure import calculate_subplot_layout

warnings.warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)


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
