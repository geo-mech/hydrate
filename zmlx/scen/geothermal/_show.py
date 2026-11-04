"""井截面取热模型的**结果绘图**（``show``）.

把一张 x–z 剖面上的物理量画成 2×2 的四张子图，并可叠加任意多个参考圆：

============  ==========================  ==================================
子图           数据                        来源
============  ==========================  ==================================
岩石温度       单元属性 ``temperature``    ``tfc.get_ca(model, ...)``
流体温度       第 0 号流体的 ``temperature``  ``tfc.get_fa(model, 0, ...)``
密度           第 0 号流体的密度           ``tfc.get_den(model, 0, ...)``
流体 z0        第 0 号流体的辅助变量 ``z0``  ``tfc.get_fa(model, 0, 'z0')``
============  ==========================  ==================================

``z0`` 是 ``_well_cross_section.create`` 里记下的单元初始 z 坐标，用来追踪流体
的运动轨迹（物质输运）。

绘图走 :func:`zmlx.ui.plot`：界面里有标签页就开标签页，无界面时存文件，
都没有则 ``plt.show()``。
"""

import numpy as np

from zmlx import add_axes2, add_items, item, linspace, plot, tfc


def _as_circles(circles):
    """把用户给的 ``circles`` 统一成 ``[(x, z, r, style), ...]``.

    允许的两种写法（可以混用）::

        (x, z, r, 'r--')                    # 元组简写：圆心 + 半径 + 线形
        dict(x=.., z=.., r=.., color='r')   # 字典：圆心 + 半径 + 任意 plot 关键字

    Args:
        circles: ``None``（用默认圆）、单个元组/字典（只画一个）、
            或由它们组成的列表/元组（画多个）。

    Returns:
        list[tuple]: 每个元素是 ``(x, z, r, style)``，其中 ``style`` 是**位置参数字符串**
        或 **dict**（plot 的关键字）。

    Raises:
        TypeError: 元素既不是元组/列表也不是字典。
        ValueError: 元组的长度不是 3 或 4、字典缺少 x/z/r、或半径不是正数。

    ⚠️ 「单个圆」与「多个圆」的判定：第一层是**数字**时（``(0.1, -0.5, 0.2)``），
    说明它本身就是一个圆；否则视为列表。这样 ``circles=(0.1, 0, 0.2, 'r--')``
    与 ``circles=[(0.1, 0, 0.2, 'r--')]`` 都能用。
    """
    if circles is None:  # 默认：原算例标示高低温区的两个参考圆
        return [(0.1, -0.5, 0.2, "r--"), (-0.1, 0.5, 0.2, "k--")]

    # 单个圆：第一层里是数字（说明直接给了 x, z, r, ...）
    if isinstance(circles, dict) or (
        isinstance(circles, (tuple, list))
        and len(circles) > 0
        and isinstance(circles[0], (int, float, np.integer, np.floating))
        and not isinstance(circles[0], bool)
    ):
        circles = [circles]

    result = []
    for one in circles:
        if isinstance(one, dict):
            try:
                x, z, r = one["x"], one["z"], one["r"]
            except KeyError as err:
                raise ValueError(
                    f"字典形式的圆必须含 x / z / r，缺少 {err}：{one}"
                ) from err
            style = {k: v for k, v in one.items() if k not in ("x", "z", "r")}
        elif isinstance(one, (tuple, list)):
            if len(one) == 3:
                x, z, r = one
                style = {}
            elif len(one) == 4:
                x, z, r, style = one
                if not isinstance(style, (str, dict)):
                    raise TypeError(
                        f"第四个元素应为线形字符串或 dict，实际是 {type(style).__name__}：{one}"
                    )
            else:
                raise ValueError(
                    f"圆应写成 (x, z, r) 或 (x, z, r, 线形)，实际长度 {len(one)}：{one}"
                )
        else:
            raise TypeError(
                f"圆应为元组/列表或 dict，实际是 {type(one).__name__}：{one}"
            )

        if not r > 0:
            raise ValueError(f"半径必须为正，实际是 {r}（圆：{one}）")
        result.append((x, z, r, style))
    return result


def _circle_items(circles):
    """把 ``[(x, z, r, style), ...]`` 转成可以传给 ``add_axes2`` 的绘图项.

    Args:
        circles: :func:`_as_circles` 的返回值。

    Returns:
        list: ``item('xy', ...)`` 的结果列表，可直接 ``*`` 展开进 ``add_axes2``。
    """
    angles = linspace(0, np.pi * 2, 100)  # 100 点在常规尺寸下已看不出棱角
    cos, sin = np.cos(angles), np.sin(angles)
    items = []
    for x, z, r, style in circles:
        cx, cz = r * cos + x, r * sin + z
        if isinstance(style, dict):
            items.append(item("xy", cx, cz, **style))
        elif len(style) > 0:
            items.append(item("xy", cx, cz, style))
        else:
            items.append(item("xy", cx, cz))
    return items


def show(model, jx, jz, caption=None, *, circles=None):
    """把模型当前状态画成一幅 2×2 的子图，并在其上叠加参考圆.

    四张子图依次是：**岩石温度**、**流体温度**、**密度**、**流体 z0**
    （各自的数据来源见模块文档）。

    Args:
        model: 要显示的模型（``Seepage``）。
        jx: x 方向的网格数量。与建网时给的一致，用于把单元数据按
            ``[jx, jz]`` 重塑成二维矩阵。
        jz: z 方向的网格数量。
        caption: 图的标题，``None`` 时不加标题。
        circles: 要叠加在**每张子图**上的圆。``None``（默认）画原算例标示高低温区的
            两个参考圆（圆心 ``(0.1, -0.5)`` / ``(-0.1, 0.5)``、半径 ``0.2``）；
            传 ``[]`` 则不画任何圆。多种写法见下方示例。

    Returns:
        None。本函数只负责把图画出来 —— 具体落在哪里由 :func:`zmlx.ui.plot` 决定：
        界面里有标签容器就开标签页；无界面则存成文件；两者都没有时 ``plt.show()``。

    Raises:
        ValueError: ``circles`` 里的半径不是正数、元组长度不是 3 或 4、
            或字典缺少 ``x`` / ``z`` / ``r``。
        TypeError: ``circles`` 的元素既不是元组/列表也不是字典，
            或第 4 个元素既不是字符串也不是字典。

    circles 的写法
    --------------
    每个圆描述「圆心 ``(x, z)`` + 半径 ``r`` + 线形」，可以给**多个**，两种写法可混用::

        # 简写元组：(x, z, r) 或 (x, z, r, '线形字符串')
        show(model, jx, jz, circles=[(0.1, -0.5, 0.2, 'r--'), (-0.1, 0.5, 0.2, 'k--')])

        # 字典：x / z / r 之外的键原样传给 matplotlib 的 plot
        show(model, jx, jz, circles=[
            dict(x=0.1, z=-0.5, r=0.2, color='red', ls='--', lw=1.5),
            dict(x=-0.1, z=0.5, r=0.2, color='black', ls=':', label='低温区'),
        ])

        # 只画一个时可以直接给，不必套列表
        show(model, jx, jz, circles=(0.0, 0.0, 0.5, 'g-'))

        # 不画圆
        show(model, jx, jz, circles=[])

    ⚠️ 线形走 matplotlib 的 ``plot``：``'r--'`` 这类**位置字符串**或
    ``color`` / ``ls`` / ``lw`` / ``alpha`` 等**关键字**都可用。

    ⚠️ 早期版本的 ``with_circle`` 参数**已移除**，改用 ``circles``：
    原 ``with_circle=False`` 等价于现在的 ``circles=[]``。
    """

    circles = _as_circles(circles)

    def on_figure(figure):
        """绘图回调：在给定 figure 上画出四张子图（由 ``plot`` 调起）.

        Args:
            figure: matplotlib 的 ``Figure`` 对象。
        """
        from zmlx.plt import calculate_subplot_layout

        nrows, ncols = calculate_subplot_layout(4, 1.0, fig=figure)  # 自动计算子图布局
        opts = dict(nrows=nrows, ncols=ncols, xlabel="x", ylabel="z", aspect="equal")
        x = tfc.get_x(model, shape=[jx, jz])  # 获取x坐标矩阵
        z = tfc.get_z(model, shape=[jx, jz])  # 获取z坐标矩阵
        args = [
            "contourf",
            x,
            z,
        ]  # 填充等值线图的基础参数

        # 圆圈：作为边界参考线叠加在每张子图上
        circle = _circle_items(circles)

        # 储层温度
        r_temp = item(
            *args,
            tfc.get_ca(model, "temperature", shape=[jx, jz]),
            cbar=dict(label="岩石温度", shrink=0.6),
        )

        # 温度分布等值线图
        f_temp = item(
            *args,
            tfc.get_fa(model, 0, "temperature", shape=[jx, jz]),
            cbar=dict(label="流体温度", shrink=0.6),
        )

        # 密度分布等值线图
        den = item(
            *args,
            tfc.get_den(model, 0, shape=[jx, jz]),
            cbar=dict(label="密度", shrink=0.6),
        )
        # z0辅助变量分布等值线图（反映流体运动导致的物质输运）
        z0 = item(
            *args,
            tfc.get_fa(model, 0, "z0", shape=[jx, jz]),
            cbar=dict(label="z0", shrink=0.6),
        )

        # 创建三个子图，分别显示温度、密度和z0，并叠加区域边界线
        add_axes2(figure, add_items, r_temp, *circle, title="岩石温度", index=1, **opts)
        add_axes2(figure, add_items, f_temp, *circle, title="流体温度", index=2, **opts)
        add_axes2(figure, add_items, den, *circle, title="密度", index=3, **opts)
        add_axes2(figure, add_items, z0, *circle, title="流体z0", index=4, **opts)

    # 执行绘图
    plot(
        on_figure,
        caption=caption,
        clear=True,
        tight_layout=True,
        suptitle=f"time = {tfc.get_time(model, as_str=True)}",
    )
