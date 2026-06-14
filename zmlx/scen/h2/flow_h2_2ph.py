# ** desc = '氢水两相流动'

from zmlx import *
from zmlx.io import opath
import numpy as np

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


#创建模型
def create(
        perm=1.0e-15,
        mesh=None,
        s_ini=None,
        save_dt_min=None,
        save_dt_max=None,
        years_max=200.0,
        **opts
):
    """
    创建模型(返回Seepage对象).
    """
    if mesh is None:  
        mesh = create_cylinder(x=np.linspace(0, 0.276, 20),
                           r=np.linspace(0, 0.0189, 10))
        swap_yz(mesh)

    # 找到上下范围，从而去找到顶底的边界
    x_min, x_max = mesh.get_pos_range(0)
    z_min, z_max = mesh.get_pos_range(2)

    def is_right(x, y, z):
        return abs(x - x_max) < 0.0001

    def is_upper(x, y, z):
        return abs(z - z_max) < 0.0001
   
    def is_prod(x, y, z):
        return abs(y - 10) < 0.1

    def get_s(x, y, z):
        if is_prod(x, y, z) and is_upper(x, y, z):
            return {'h2o': 1}
        else:
            return {'h2o': 0.15, 'h2': 0.85}
            
    def denc(*pos):
        return 1e20 if is_upper(*pos) else 3e6

    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来.
        return 1.0 if abs(y) < 2 else 0.0
     
    def porosity(*pos):  
        return 0.0001 if is_upper(*pos) else 0.18
        
    def get_idx(x, y, z):
        return 0
        
    def inj_cells(model):
        injectors = []
        for cell in model.cells:
            if abs(cell.x - x_min) < 0.0001 and not is_upper(*cell.pos):
               injectors.append(cell.pos)
        return injectors
       
    # 添加虚拟的cell和face用于生产
    producers = []
    for cell in mesh.cells:
        (x,y,z) = cell.pos
        if is_right(x,y,z) and not is_upper(x,y,z):
            pos, offset = [x, 0, z], [0, 10, 0]            
            add_cell_face(mesh, pos=pos, offset=offset, vol=1.0e6,
                  area=0.0138, length=0.035)
            producers.append(mesh.get_nearest_cell([pos[i] + offset[i] for i in range(3)]).index)
     
    # 创建模型
    model = seepage.create(
        gravity=[0, 0, -9.8],
        dt_min=60,
        dt_max=3600 * 3,
        dv_relative=0.1,
        mesh=mesh,
        porosity=porosity,
        pore_modulus=100e6,
        denc=denc,
        temperature=273.15 + 30.0,
        p=3e6,
        s=get_s,
        perm=1.07e-13,
        dist=0.001,
        fludefs=[create_h2(name='h2'),
                 create_h2o(name='h2o')],
        heat_cond=heat_cond,
        prods=[{'index': producers[i],
                't': [0, 1e20],
                'p': [1.01e5, 1.01e5]} for i in range(len(producers))]
                )
  
    # 用于solve的选项
    model.set_text(
        key='solve',
        text={
              'show_cells': {'dim0': 0,
                             'dim1': 2,
                             'mask': seepage.get_cell_mask(
                                 model=model, yr=[-1, 1])},
              'time_max': 3 * 3600 ,
              'save_dt_min':  3600 * 0.2, 
              'save_dt_max':  3600 * 3,
              }
    )

    # 设置相渗
    i_h2 = model.find_fludef('h2')[0]
    i_h2o = model.find_fludef('h2o')[0]

    x, y = parse_coordinates(krw_data) 
    model.set_kr(i_h2, kr=Interp1(x=x, y=y))

    x, y = parse_coordinates(krw_data)
    model.set_kr( i_h2o, kr=Interp1(x=x, y=y))
    
    #设置毛细管压力
    capillary.add_setting(
        model, fid0='h2', fid1='h2o', get_idx=get_idx, data=[Pc_data]
    )

    
    # 设置注入点 (h2和h2o).
    injectors = inj_cells(model)

    for i in range(len(injectors)):
        seepage.add_injector(
            model, data=dict(
                flu='insitu',
                fluid_id='h2',
                value=0.02*1.0e-6/(60*len(injectors)),  # m^3/s
                pos=injectors[i],
            ))

        seepage.add_injector(
            model, data=dict(
                flu='insitu',
                fluid_id='h2o',
                value=0.98*1.0e-6/(60*len(injectors)),  # m^3/s
                pos=injectors[i],
            ))
        
    return model


def show(model: Seepage):
    hydrate.show_2d_v2(
        model, dim0=0, dim1=2,
        fids=['h2', 'h2o'],
    )


def solve(model, *args, extra_plot=None, **kwargs):
    def x():
        show(model)
        if callable(extra_plot):
            extra_plot()
            
    seepage.solve(model, *args, extra_plot=x, **kwargs)


def main():
    model = create()
    solve(
        model, folder=opath('result', 'h2_2phs_4'), close_after_done=False,
    )


if __name__ == '__main__':
    main()
