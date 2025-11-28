from typing import Optional

from zml import SeepageMesh
from zmlx.plt.cbar import add_cbar


def add_seepage_mesh(
        ax, mesh: SeepageMesh, *,
        cell_scale: float = 1.0,
        cell_alpha: float = 0.8,
        face_color='gray',
        face_alpha: float = 0.5,
        face_linewidth: float = 0.5,
        cbar: Optional[dict] = None
):
    """
    在 matplotlib 图形上绘制"渗流网格"（三维视图）

    Args:
        ax (matplotlib.axes.Axes): 目标坐标轴
        mesh (SeepageMesh): 渗流网格对象
        cell_scale (float): Cell散点大小缩放因子
        cell_alpha (float): Cell透明度
        face_color (str): 面线段颜色
        face_alpha (float): 面线段透明度
        face_linewidth (float): 面线段宽度
        cbar: 显示colorbar的参数. 比如 dict(label=..., title=...)
    """
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Line3DCollection

    # 收集Cell数据
    cell_positions = []
    cell_volumes = []

    # 遍历所有Cell
    for cell in mesh.cells:
        pos = cell.pos
        cell_positions.append(pos)
        cell_volumes.append(cell.vol)

    cell_positions = np.array(cell_positions)
    cell_volumes = np.array(cell_volumes)

    # 绘制Cell散点（颜色代表体积）
    if len(cell_volumes) > 0:
        min_vol = float(np.min(cell_volumes))
        max_vol = float(np.max(cell_volumes))
        if min_vol == max_vol:
            sizes = np.ones_like(cell_volumes)
        else:
            sizes = cell_scale * (cell_volumes - min_vol) / (max_vol - min_vol) + 1.0

        sc = ax.scatter(
            cell_positions[:, 0],
            cell_positions[:, 1],
            cell_positions[:, 2],
            c=cell_volumes,
            s=sizes,
            alpha=cell_alpha,
        )
        if isinstance(cbar, dict):
            add_cbar(ax, obj=sc, **cbar)
    else:
        sc = None

    # 收集面数据
    face_lines = []

    # 遍历所有面
    for face in mesh.faces:
        # 获取面连接的两个Cell
        cell0 = face.get_cell(0)
        cell1 = face.get_cell(1)

        # 获取位置
        pos0 = cell0.pos
        pos1 = cell1.pos

        # 添加到线段列表
        face_lines.append([pos0, pos1])

    # 使用线段集合绘制面（效率更高）
    if face_lines:
        lc = Line3DCollection(
            face_lines,
            colors=face_color,
            linewidths=face_linewidth,
            alpha=face_alpha
        )
        ax.add_collection(lc)
    else:
        lc = None

    return sc, lc


def test():
    """
    测试
    """
    from zmlx import create_cube, plot, add_axes3
    import random
    import numpy as np

    mesh = create_cube(
        x=np.linspace(0, 10, 30),
        y=np.linspace(0, 20, 50),
        z=[-1, 1])

    for c in mesh.cells:
        c.vol = random.uniform(0.5, 5)
        x, y, z = c.pos
        z = np.sin(x / 5) * np.cos(y / 5) * 3
        c.pos = [x, y, z]

    plot(add_axes3, add_seepage_mesh, mesh,
         cbar=dict(label='Volume', shrink=0.5),
         gui_mode=True,
         aspect='equal', xlabel='x', ylabel='y', zlabel='z', title=f'A Seepage Mesh'
         )


if __name__ == '__main__':
    test()
