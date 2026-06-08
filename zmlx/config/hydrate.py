from zmlx.scen.hydrate import *

_keep = [create_caps, create_fludefs, create_opts]


def create(*args, **kwargs):
    """
    在旧的版本中，create函数用于创建配置对象。已废弃。
    """
    warnings.warn(
        "The function create() will be removed in future version", DeprecationWarning, stacklevel=2)
    return Config(*args, **kwargs)


import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)
