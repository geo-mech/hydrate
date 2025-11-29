from zmlx.config.seepage import create as create_seepage_model
from zmlx.exts.base import FractureNetwork, Seepage
from zmlx.frac.mesh import create_mesh


def create_flow(
        network: FractureNetwork, *,
        fludefs,
        s,
        mesh_opts=None,
        **opts) -> Seepage:
    """
    根据固体的裂缝网络，创建对应的流体系统模型（三维的网络，在z方向有多层）.
    这里，将主要依赖seepage模块来完成.
    这样做的好处，从而确保生成的模型
    满足直接在seepage中iterate的要求。
    """
    if mesh_opts is None:
        mesh_opts = {}

    # 创建渗流的网格
    mesh = create_mesh(network, **mesh_opts)

    # 一些默认的参数
    default_opts = dict(
        p=1.0e6,
        temperature=285.0,
        denc=1.0e5,
        pore_modulus=100e6,
        porosity=1.0,
        dt_min=1.0e-3,
        dt_max=24.0 * 3600.0,
        dv_relative=0.2,
        perm=1.0e-14,
        tags=['disable_ther', 'disable_heat_exchange']
    )
    opts = {**default_opts, **opts}  # opts中的值会覆盖默认值

    return create_seepage_model(
        mesh=mesh,
        fludefs=fludefs,
        s=s,
        **opts
    )
