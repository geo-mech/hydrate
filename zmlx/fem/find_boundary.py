from zml import DynSys


def find_boundary(dyn: DynSys, n_dim, i_dim, lower, i_dir, eps=None):
    """
    找到边界自由度的序号(作为list返回).
        n_dim: 模型的总维度 (1, 2, 3)
        i_dim: 目标边界的维度 (0, 1, 2)
        lower: 在目标维度下，是查找左侧边界(lower)还是右侧边界
        i_dir: 在目标边界上，取哪个方向的自由度
    -- 2023.12.6
    """
    assert n_dim == 1 or n_dim == 2 or n_dim == 3
    assert i_dim == 0 or i_dim == 1 or i_dim == 2
    assert i_dir == 0 or i_dir == 1 or i_dir == 2
    assert i_dim < n_dim
    assert i_dir < n_dim

    size = dyn.size

    pos = 1.0e100 if lower else -1.0e100
    idx = i_dim
    while idx < size:
        pos = min(pos, dyn.get_pos(idx)) if lower else max(pos, dyn.get_pos(idx))
        idx += n_dim

    if eps is None:
        eps = 1.0e-6

    ids = []
    idx = i_dim
    while idx < size:
        if abs(pos - dyn.get_pos(idx)) <= eps:
            ids.append(idx + (i_dir - i_dim))
        idx += n_dim

    return ids

