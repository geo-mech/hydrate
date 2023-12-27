import sys

sys.path.append("./hydrate/")

from zmlx import *
import numpy as np
from zmlx.react import melt


gas = 0
sol = 1

soil_thick = 2
ice_thick = 1
gas_thick = 3


def create(soil_thick, ice_thick, gas_thick):
    # 创建模型
    model = Seepage()
    # 创建网格
    mesh = SeepageMesh.create_cube(
        x=np.linspace(-100, 100, 101), y=np.linspace(-100, 100, 101), z=(-0.5, 0.5)
    )

    # 创建二氧化碳升华/凝华反应   参考温度：升华点
    r = melt.create(
        sol=sol,
        flu=gas,
        vp=[1, 100e6],
        vt=[105, 105],
        temp=105,
        heat=573000,
        fa_t=model.reg_flu_key("t"),
        fa_c=model.reg_flu_key("c"),
        t2q=([-10, 0, 10], [-1, 0, 1]),
        l2r=True,
        r2l=False,  # 和melt相比，方向改变
    )
    model.add_reaction(r)

    # 添加cells
    for c in mesh.cells:
        cell = model.add_cell()
        assert isinstance(cell, Seepage.Cell)
        cell.pos = c.pos

        cell.fluid_number = 2
        # 定义co2气体质量、温度、比热
        cell.get_fluid(0).mass = gas_thick * 1.977
        cell.get_fluid(0).set_attr(model.reg_flu_key("t"), 100)
        cell.get_fluid(0).set_attr(model.reg_flu_key("c"), 846)

        # 定义co2ice质量、温度、比热
        cell.get_fluid(1).mass = soil_thick * 1560
        cell.get_fluid(1).set_attr(model.reg_flu_key("t"), 100)
        cell.get_fluid(1).set_attr(model.reg_flu_key("c"), 840)

        # 定义下伏冰层温度、mc
        cell.set_attr(model.reg_cell_key("t"), 100)
        cell.set_attr(model.reg_cell_key("mc"), ice_thick * 920 * 2090)
        
        # 定义背景交换参数
        cell.set_attr(model.reg_cell_key("mc_b"), 1e10)
        cell.set_attr(model.reg_cell_key("t_b"), 100)
        cell.set_attr(model.reg_cell_key("g_heat_b"), 0.3)
        
        # 定义加热功率
        cell.set_attr(model.reg_cell_key("p"), 0)

        # 定义冰层与二氧化碳冰之间的交换热系数
        cell.set_attr(model.reg_cell_key("g_heat"), 30)

    # 添加faces
    for f in mesh.faces:
        face = model.add_face(model.get_cell(f.link[0]), model.get_cell(f.link[1]))
        # heat conductivity = 1.5
        face.set_attr(model.reg_face_key("g"), f.area * 1.5 / f.length)
    return model


def solve(model: Seepage):
    # 时间步长
    dt = 50000

    # 给一个加热功率的扰动点
    # d = [0,20,40]
    for i in range(1):
        # x = d[i]
        # y = d[i]
        x = np.random.uniform(-90, 90)
        y = np.random.uniform(-90, 90)
        cell = model.get_nearest_cell([0, 0, 0])
        cell.set_attr(model.reg_cell_key("p"), 800)
        
    powers0 = model.numpy.cells.get(model.reg_cell_key("p"))

    # 初始co2ice质量
    init_mass = soil_thick * 1560

    for step in range(1000001):
        print(f"step = {step}/1000000")
        # 能量分配顺序
        # 1、接受太阳辐射
        # 2、能量全部传递给co2ice
        # 3、基底温度平衡
        # 4、co2ice冰背景冷却
        
        # 太阳辐射能量
        model.heating(
            ca_mc=model.reg_cell_key("mc"),
            ca_t=model.reg_cell_key("t"),
            ca_p=model.reg_cell_key("p"),
            dt=dt,
        )
        
        # 热量交换
        model.exchange_heat(
            dt=dt,
            ca_g=model.reg_cell_key("g_heat"),
            ca_t=model.reg_cell_key("t"),
            ca_mc=model.reg_cell_key("mc"),
            fa_t=model.reg_flu_key("t"),
            fa_c=model.reg_flu_key("c"),
        )
        
        # 热量交换 背景冷却
        model.exchange_heat(
            dt=dt,
            ca_g=model.reg_cell_key("g_heat_b"),
            ca_t=model.reg_cell_key("t_b"),
            ca_mc=model.reg_cell_key("mc_b"),
            fa_t=model.reg_flu_key("t"),
            fa_c=model.reg_flu_key("c"),
        )
        

        # 升华凝华
        model.get_reaction(0).react(model, dt=dt)


        # 重设二氧化碳气体为 1 kg
        model.numpy.fluids(gas).mass = gas_thick * 1.977

        # # 更新加热功率 mass 应取CO2ice的mass
        mass = model.numpy.fluids(1).mass
        powers = powers0 * (1 + (init_mass - mass) / init_mass)
        model.numpy.cells.set(model.reg_cell_key("p"), powers)
        
        
        # 温度平衡
        model.iterate_thermal(
            dt=dt,
            ca_t=model.reg_cell_key("t"),
            ca_mc=model.reg_model_key("mc"),
            fa_g=model.reg_face_key("g"),
        )

        # 输出数据
        if step % 2000 == 0:
            path = make_fpath("cool-0.3", step=step)
            with open(path, "w") as file:
                for cell in model.cells:
                    x, y, z = cell.pos
                    # 输出文件顺序为 x, y, z, co2ice_mass, co2ice_t, co2_t, ice_p, ice_t,
                    file.write(
                        f'{x}\t{y}\t{z}\t{cell.get_fluid(1).mass}\t{cell.get_fluid(1).get_attr(model.reg_flu_key("t"))}\t{cell.get_fluid(0).get_attr(model.reg_flu_key("t"))}\t{cell.get_attr(model.reg_cell_key("p"))}\t{cell.get_attr(model.reg_cell_key("t"))}\t{cell.get_attr(model.reg_cell_key("t_b"))}'
                    )
                    file.write("\n")


if __name__ == "__main__":
    model = create(soil_thick, ice_thick, gas_thick)
    solve(model)

