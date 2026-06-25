# ** desc = '氢水两相流动'
#问题说明：
#初始模型不稳定，虽然压力相等，
#如果右端大体积网格水饱和度为0，但水和气会自发流向右侧网格，导致左侧模拟岩芯的网格没有水。
#如果右端大体积网格水饱和度为1.0，水会从右侧网格向左流，导致左侧模拟岩芯的网格饱和水水。
#就是左侧小体积网格的水饱和度会变得和右侧大体积网格相同。
#压力是相等的，且不考虑毛细管压力，为什么会发生流动？


from zmlx import *
from zmlx.io import opath
import numpy as np

from zmlx.demo.h2_2phs.h2 import create as create_h2

sw = np.linspace(0.15,1.0,20)
swn = (sw-0.15)/(1-0.15)

# 相对渗透率曲线数据
krg =  0.61*(1-swn)**1.6/((1-swn)**1.6+6.0*swn**0.9)
krw =  1.0*swn**7.5/(swn**7.5+2.95*(1-swn)**0.52)

krg_data, krw_data = '', ''
for i in range(len(sw)):
    krg_data += str(sw[i])+' '+str(krg[i])+'\n'
    krw_data += str(sw[i])+' '+str(krw[i])+'\n'


# 毛细管压力曲线数据
swx = (sw-0.15)/(1-0.15)
P_cap = (1.4e6-5.0e3)*(1-swx)**1.0/((1-swx)**1.0+130.0*swx**1.0)+5.0e3
P_cap =  np.where(sw==1.0,0.0,P_cap)

# 第一列，Gas的饱和度  第二列, Gas压力-Water压力
Pc_data = ''
for i in range(len(sw)-1,-1,-1):
    Pc_data += str(1-sw[i])+' '+str(P_cap[i])+'\n'


def parse_coordinates(input_str):
    """
    将输入字符串解析为两个列表，分别包含x和y坐标，并将x坐标从小到大排序。
    参数:
    input_str (str): 包含坐标数据的字符串
    返回:
    tuple: 包含两个列表的元组，第一个列表包含排序后的x坐标，第二个列表包含对应的y坐标
    """
    lines = input_str.strip().split('\n')
    coordinates = []

    for line in lines:
        x, y = map(float, line.split())
        coordinates.append((x, y))

    # 根据x坐标对坐标列表进行排序
    coordinates.sort(key=lambda coord: coord[0])
    x_values = [coord[0] for coord in coordinates]
    y_values = [coord[1] for coord in coordinates]

    return x_values, y_values


def create(jx: int, jy: int) -> Seepage:
    """
    创建模型.
    Args:
        jx: 模型的x方向的单元格数量
        jy: 模型的y方向的单元格数量

        
    Returns:
        model: 模型对象
    """

    mesh: SeepageMesh = create_cylinder(
        x=linspace(0, 0.276+(0.276/jx), jx + 2),
        r=linspace(0, 0.0189, jy + 1)
    )

    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x1) < 0.0001:
            cell.vol = 1.0e8
     
    def is_prod(x, y, z):
        return abs(x - x1) < 0.0001

    def get_p(x, y, z) :
        return 3e6
 
       
    def get_s(x, y, z):
        if is_prod(x, y, z):
            return {'h2o': 0.0, 'h2': 1.0}
        else:
            return {'h2o': 0.15, 'h2': 0.85}
 
#    def get_idx(x, y, z):
#        return 0    

    # 创建模型
    model = seepage.create(
        dt_min=10,
        dt_max=3600 * 2,
        dv_relative=0.1,
        mesh=mesh,
        porosity=0.18,
        pore_modulus=100e6,
        temperature=273.15 + 30.0,
        p=get_p,
        s=get_s,
        perm=1.07e-13,
        disable_ther=True,
        disable_heat_exchange=True,
        fludefs=[create_h2(name='h2'),
                 create_h2o(name='h2o')]
                ) 

    # 用于solve的选项
    model.set_text(
        key='solve',
        text={
              'save_dt_min':  3600 * 0.5, 
              'save_dt_max':  3600 * 2,
              }
    )    
    
    # 找到需要注入的单元
    ca_vol = model.get_cell_key('vol')
    all_vol = 0
    cells_inj = []
    for c in model.cells:
        if abs(c.x - x0) < 0.001:
            cells_inj.append(c)
            all_vol += c.get_attr(ca_vol)    

    # 设置相渗
    i_h2 = model.find_fludef('h2')[0]
    i_h2o = model.find_fludef('h2o')[0]

    x, y = parse_coordinates(krw_data) 
    model.set_kr(i_h2, kr=Interp1(x=x, y=y))

    x, y = parse_coordinates(krw_data)
    model.set_kr( i_h2o, kr=Interp1(x=x, y=y))
    
    #设置毛细管压力
#    capillary.add_setting(
#        model, fid0='h2', fid1='h2o', get_idx=get_idx, data=[Pc_data]
#    )

    
    # 设置注入点 (h2和h2o). 
    for cell in cells_inj:
        model.add_injector(
            fluid_id=0,
            flu=cell.get_fluid(0),
            pos=cell.pos,
            radi=0.1,
            opers=[(0, (0.0*1.0e-6/60) * cell.get_attr(ca_vol) / all_vol)]
        )

        model.add_injector(
            fluid_id=1,
            flu=cell.get_fluid(1),
            pos=cell.pos,
            radi=0.1,
            opers=[(0, (0.0*1.0e-6/60) * cell.get_attr(ca_vol) / all_vol)]
        )
        
    return model


def show(model: Seepage, jx: int, jy: int):
    """
    在界面上显示模型的状态.
    Args:
        model: 模型对象
        jx: 模型的x方向的单元格数量
        jy: 模型的y方向的单元格数量
    """
    x = tfc.get_x(model, shape=(jx+1, jy))
    y = tfc.get_y(model, shape=(jx+1, jy))
    p = tfc.get_p(model, shape=(jx+1, jy))
    s = tfc.get_v(model, 1, shape=(jx+1, jy)) / tfc.get_v(model, None, shape=(jx+1, jy))

    def on_figure(figure):
        layout = AutoFigLayout(figure, 2, 3.0, xlabel='x/m', ylabel='r/m', aspect='equal')
        layout.add_axes2(
            add_contourf, x, y, p, cbar=dict(label='Pressure', shrink=0.7), title='Pressure'
        )
        layout.add_axes2(
            add_contourf, x, y, s, cbar=dict(label='Saturation', shrink=0.7), cmap='coolwarm', title='Saturation'
        )

        
    plot(on_figure, caption=f'Seepage({model.handle_str})', tight_layout=True)


def main():
    """
    执行建模并且求解的主函数
    """
    jx, jy = 50, 20
    model = create(jx, jy)
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy), time_forward=10 * 3600,folder=opath('result', 'h2_2phs_5'))

    
if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
