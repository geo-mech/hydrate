"""
处理对matplotlib的操作。

主要包括以下函数：

基础函数:
    plot_on_figure: 接收一个针对figure的回调函数，在figure上绘图，并自动显示在 zmlx.ui中. 此函数是其他操作的基础.
    plot_on_axes: 接收一个针对Axes的回调函数，在Axes上绘图，并自动显示在 zmlx.ui中

针对Axes的函数.  将对象添加到Axes上, 函数名称为 add_xxx的形式，主要包括：
    add_curve: 添加曲线
    add_contourf: 添加等值线
    add_tricontourf: 添加三角等值线
    add_trisurf: 添加三角表面
    add_fn2: 添加函数2
    add_surf: 添加表面
    add_legend: 添加图例
    ......
    后续会添加其它add_xxx形式的函数.

绘制单个图。直接在zmlx.ui的界面上，在一个标签页面绘制单个图. 函数名称为 show_xxx的形式，比如：
    show_dfn2: 显示离散裂缝网络
    show_fn2: 显示裂缝网络
    show_field2: 显示场
    ……
    后续，会添加其他show_xxx形式的函数.

其它辅助函数，比如：
    calc_best_layout/calculate_subplot_layout: 计算最佳子图布局
    get_cm: 获取颜色映射表
    get_color: 获取颜色
    ...
    此类辅助函数比较有限。

除了以上几类函数之外，plt包中的其它内容，将逐渐废弃.
"""

from zmlx.exts import SelfPath
from zmlx.plt.cmap import get_cm, get_color

# 添加对象到Axes上, add_xxx形式的函数
from zmlx.plt.on_axes import (
    add_curve,
    add_curve as add_curve2,
    add_curve as curve,
    add_cbar,
    add_contourf,
    add_tricontourf,
    add_trisurf,
    add_fn2,
    add_surf,
    add_legend,
    add_dfn2,
    add_seepage_mesh,
    add_scatter,
)

# 在figure上添加子图. add_axes 形式的函数
from zmlx.plt.on_figure import (
    AutoLayout,
    add_subplot,
    add_axes2,
    add_axes3,
    plot_on_figure,
    plot_on_axes,
    calc_best_layout,
    calculate_subplot_layout,
    add_axes_img,
)

# 绘制单个图. show_xxx形式的函数
from zmlx.plt.on_ui import (
    show_tricontourf,
    show_tricontourf as tricontourf,
    show_contourf,
    show_contourf as contourf,
    show_xy,
    show_xy as plot_xy,
    show_xy as plotxy,
    show_dfn2,
    show_fn2,
    show_field2,
    show_rc3,
    show_trisurf,
    show_trisurf as plot_trisurf,
    show_trimesh,
    show_trimesh as trimesh,
    show_scatter,
    show_flu_def,
)
from zmlx.plt._font import set_chinese_font
from zmlx.plt._save import get_plt_save_path, set_plt_save_path
from zmlx.system import deprecated


@deprecated(remove_after="2027-6-1", alternative="zmlx.fig.item")
def item(*args, **kwargs):
    from zmlx.fig import item as impl

    return impl(*args, **kwargs)


@deprecated(remove_after="2027-6-1", alternative="zmlx.fig.plot3d")
def plot3d(*args, **kwargs):
    from zmlx.fig import plot3d as impl

    return impl(*args, **kwargs)


@deprecated(remove_after="2027-6-1", alternative="zmlx.fig.plot2d")
def plot2d(*args, **kwargs):
    from zmlx.fig import plot2d as impl

    return impl(*args, **kwargs)


get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
