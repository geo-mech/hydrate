from zml import FractureNetwork
from zmlx.config.seepage import create as create_seepage_model
from zmlx.kit.frac import layer as layer_alg
from zmlx.kit.frac.create_seepage_mesh import create_seepage_mesh


def create_flow(
        network: FractureNetwork,
        fludefs, ini_sat,
        lave,
        z_min, z_max,  # 基于network的坐标体系
        layer_n,  # 默认仅仅包含1层，即等于与2D模型的效果
        aperture=0.01,
        pressure=1.0e6,
        perm=1.0e-14,
        dt_min=1.0e-3,
        dt_max=24.0 * 3600.0,
        dv_relative=0.2,
        injectors=None,
        **kw):
    """
    根据固体的裂缝网络，创建对应的流体系统模型（三维的网络，在z方向有多层）.
    这里，将主要依赖seepage模块来完成.
    这样做的好处，从而确保生成的模型
    满足直接在seepage中iterate的要求。
    """
    # todo: 对于输入参数，进行必要的检查
    assert layer_n > 0

    layer_h = (z_max - z_min) / layer_n  # 每一层的厚度

    # 计算Seepage对象的Cell和Face的参数
    cell_vol = aperture * layer_h * lave
    face_s1 = aperture * layer_h  # 连接水平方向的Face的面积
    face_l1 = lave  # 连接水平方向的Face的长度

    mesh = create_seepage_mesh(
        network=network,
        cell_vol=cell_vol, face_area=face_s1, face_dist=face_l1
    )
    pore_modulus = 100e6  # 孔隙刚度

    # 各个小层的模型
    layers = [create_seepage_model(
        mesh=mesh,
        fludefs=fludefs,
        porosity=1.0,  # 全部被流体填充
        pore_modulus=pore_modulus,  # 孔隙刚度
        denc=1.0e5,  # 相对小的热容量
        temperature=285.0,
        p=pressure,
        s=ini_sat,
        perm=perm,  # 渗透率
        dt_min=dt_min, dt_max=dt_max, dv_relative=dv_relative,
        injectors=injectors,
        **kw
    ) for _ in range(layer_n)]

    # 将各个小层的模型合成为一个模型
    model = layers[0].get_copy()
    model.clear_cells_and_faces()
    layer_alg.connect(layers, result=model)
    print(f'model = {model}')

    # 在初始的压力的情况下，体积为给定 cell_vol，后续，压力增大pore_modulus之后
    # 体积增大为 cell_vol
    k = max(1.0e-30, abs(cell_vol)) / max(1.0e-30, abs(pore_modulus))
    v0 = cell_vol - pressure * k

    # 将一些属性记录到model中 (后续，当裂缝扩展了之后，将基于这些属性来更新模型)
    model.set_attr(index='cell_v0', value=v0)
    model.set_attr(index='cell_k', value=k)
    model.set_attr(index='face_g1', value=aperture * layer_h * perm / lave)
    model.set_attr(index='face_g2', value=aperture * lave * perm / layer_h)
    model.set_attr(index='p_ini', value=pressure)
    model.set_attr(index='cell_vol', value=cell_vol)

    # 当1层的时候，兼容2D的模型
    model.set_attr(index='face_cond', value=aperture * layer_h * perm / lave)

    # todo: 暂时不处理和热相关的功能，后续需要再仔细考虑.
    model.add_tag('disable_ther')
    model.add_tag('disable_heat_exchange')

    return model
