"""
正在测试中，尚未完成。有尚未发现的bug
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gas_mig import create, show, get_fracture_mesh
from zmlx import *


def solve(model: Seepage, indexes: list, fracture_model: Seepage, time_max=None, extra_plot=None):
    """
    求解模型，并尝试将结果保存到folder.
    """

    def plot_():
        if extra_plot is not None:
            extra_plot()

    # 创建copy任务
    assert len(indexes) == model.cell_number
    source_cells = []
    target_cells = []
    for i in range(model.cell_number):
        index = indexes[i]
        if index is not None:
            source_cells.append(model.get_cell(i))
            target_cells.append(fracture_model.get_cell(index))
    assert len(target_cells) == fracture_model.cell_number
    copy_task = tfc.CellCopyTask(source_cells, target_cells)

    def iterate_all():
        if tfc.get_time(fracture_model) < tfc.get_time(model):
            copy_task.run(True)
            tfc.set_dt(fracture_model, 1.0)
            while tfc.get_time(fracture_model) < tfc.get_time(model):
                tfc.iterate(fracture_model)
                print(f'fracture_model dt={tfc.get_dt_str(fracture_model)}')
            copy_task.run(False)
        tfc.iterate(model)

    # 执行最终的迭代
    gui_iter = get_gui_iter(iterate_all, plot=plot_)

    if time_max is None:  # 给定默认值
        time_max = 1.0e100

    while tfc.get_time(model) < time_max:
        gui.break_point()
        gui_iter()

        if tfc.get_step(model) % 20 == 0:
            print(
                f'step={tfc.get_step(model)}, dt={tfc.get_dt_str(model)}, '
                f'time={tfc.get_time_str(model)}')
    plot_()


def main():
    jx, jz = 60, 100
    mesh = create_cube(
        x=linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=linspace(-500, 0, jz + 1)
    )

    model = create(mesh)

    fractures = [
        (150, -500, 30, -200)
    ]
    indexes, fracture_mesh = get_fracture_mesh(mesh, fractures)
    print(fracture_mesh)

    fracture_model = create(fracture_mesh)

    solve(model, indexes, fracture_model, extra_plot=lambda: show(model, jx, jz, caption='当前状态'),
          time_max=3600 * 24 * 365 * 6)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
