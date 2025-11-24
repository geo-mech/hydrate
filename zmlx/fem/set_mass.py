from zmlx.base.zml import DynSys


def set_mass(dyn: DynSys, ids, mas):
    """
    批量设置给定自由度的质量
    -- 2023.12.6
    """
    size = dyn.size
    for i in ids:
        if i < size:
            dyn.set_mass(i, mas)
