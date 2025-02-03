# 1D benchmark case of heat conduction


import numpy as np
from zml import Seepage
from zmlx.seepage_mesh.cube import create_cube
from zmlx.ui import gui
from zmlx.utility.SeepageNumpy import as_numpy
from zmlx.plt.plotxy import plotxy


class CellAttrs:
    temperature = 0
    mc = 1


class FaceAttrs:
    g_heat = 0


def create():
    model = Seepage()
    mesh = create_cube(np.linspace(0, 100, 501), (-0.5, 0.5), (-0.5, 0.5))
    x0, x1 = mesh.get_pos_range(0)

    for c in mesh.cells:
        cell = model.add_cell()
        cell.pos = c.pos
        x = c.pos[0]
        # T0 = 273.15 T1 = 373.15
        cell.set_attr(CellAttrs.temperature,
                      373.15 if abs(x-x0) < 1e-3 else 273.15)
        # 设置比热容 和 密度
        cell.set_attr(CellAttrs.mc, 1.0e20 * c.vol if abs(x-x0) < 1e-3 else 2640 * 754.4 * c.vol)

    for f in mesh.faces:
        # 高温高压测试结果 热导率为1.69 W/(K·m)
        face = model.add_face(model.get_cell(f.link[0]), model.get_cell(f.link[1]))
        face.set_attr(FaceAttrs.g_heat, f.area * 1.69 / f.length)

    return model


def show(model,step):
    ada = as_numpy(model)
    plotxy(ada.cells.x, ada.cells.get(CellAttrs.temperature), caption='temperature', gui_only=True)
    np.savetxt(f'./Heat1D/{step:05d}.txt',np.column_stack((ada.cells.x, ada.cells.get(CellAttrs.temperature))))

def solve(model):
    dt = 200000
    
    for step in range(5001):
        gui.break_point()
        model.iterate_thermal(dt=dt, ca_t=CellAttrs.temperature, ca_mc=CellAttrs.mc,
                              fa_g=FaceAttrs.g_heat)
        if (step*dt) % (500*24*3600) < dt:
            show(model,step)
            print(f'step = {step}') 


def execute(gui_mode=False, close_after_done=False):
    gui.execute(solve, close_after_done=close_after_done, args=(create(),), disable_gui=not gui_mode)


def plt_compr():
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.special import erf
    import os
    # 设置颜色循环
    colors = plt.cm.tab20.colors[:13]  # 使用前13个颜色
    # 定义参数
    x = np.linspace(0, 100, 101)
    T0 = 0
    T1 = 100
    k = 1.69
    rho = 2640
    c = 754.4
    alpha = k /(rho * c)
    folder = './Heat1D/'
    names = os.listdir(folder)

    # 创建图形
    fig,ax = plt.subplots(figsize=(6,3),dpi=300)

    day = 24*3600

    # 理论解
    for i,t in enumerate(np.linspace(500*day, 3000*day, 6)):
        T = T1 + (T0 - T1) * erf(x / (2 * np.sqrt(alpha * t)))
        ax.plot(x, T, c=colors[i],label=f'{t/3600/24:.0f} d')

    # 数值模拟
    step = 5  # 每隔 10 个点取一个点
    for i in [1, 2, 3, 4, 5, 6]:
        d = np.loadtxt(os.path.join(folder, names[i]))
        print(os.path.join(folder, names[i]))
        ax.plot(d[::step, 0], d[::step, 1] - 273.15, 'o', markersize=3, c=colors[i - 1])

    ax.set(xlim=(0,100),ylim=(0,100))
    ax.legend(frameon=False)
    # 显示图形
    plt.xlabel('Distance (m)')
    plt.ylabel('Temperature (℃)')
    plt.show()

if __name__ == '__main__':
    execute()
    plt_compr()

