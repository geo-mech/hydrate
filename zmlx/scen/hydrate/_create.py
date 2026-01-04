from zmlx.exts import Seepage
from zmlx.scen.hydrate._opt import create_opts
from zmlx.tfc import create as create_tfc


def create(**opts) -> Seepage:
    """
    创建水合物计算模型
    """
    opts = create_opts(**opts)
    model = create_tfc(**opts)
    return model
