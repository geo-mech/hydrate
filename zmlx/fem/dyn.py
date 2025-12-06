"""
用以构建DynSys对象
"""

from zmlx.base.zml import DynSys, LinearExpr


def create_dyn(masses: list[float], elements: list[list[int]],
               matrices, velocities=None, displacements=None):
    """
    创建DynSys对象. 其中DynSys的每一个自由度代表的是对应自由度的“位移”（或者“转角”），即相对于初始平衡位置的偏移的量。

    Args:
        masses: 自由度的质量（或者转动惯量）列表。质量（或者转动惯量）是必须给定的。
        elements: 单元列表。其中的每一个元素都是一个列表，包含了该单元关联的自由度的索引。
        matrices: 单元刚度矩阵列表，每个元素都是一个二维数组，代表该单元的刚度矩阵（矩阵的大小，等于该单元关联的自由度的数量）。
        displacements: 自由度的位移（或者转角）列表。如果为None，则默认所有自由度位移为0。
        velocities: 自由度的速度（或者角速度）列表。如果为None，则默认所有自由度速度为0。

    Returns:
        DynSys对象
    """
    n_dof = len(masses)  # 自由度的数量

    # 参数检查
    if velocities is not None:
        assert n_dof == len(velocities), "自由度的速度的数量和自由度数量必须相同"
    if displacements is not None:
        assert n_dof == len(displacements), "自由度的位移的数量和自由度数量不一致"

    # 初始化DynSys对象
    dyn = DynSys()
    dyn.size = n_dof

    # 设置初始的状态
    for i_dof in range(n_dof):
        assert masses[i_dof] > 0, f"自由度{i_dof}的质量必须大于0"
        dyn.set_mass(i_dof, masses[i_dof])  # 必须设置质量
        if velocities is None:
            dyn.set_vel(i_dof, 0)
        else:
            dyn.set_vel(i_dof, velocities[i_dof])
        if displacements is None:
            dyn.set_pos(i_dof, 0)
        else:
            dyn.set_pos(i_dof, displacements[i_dof])

    # 设置单元刚度矩阵
    assert len(elements) == len(matrices), "单元的数量必须与单元刚度矩阵的数量相同"

    for i_elem in range(len(elements)):
        element = elements[i_elem]
        matrix = matrices[i_elem]

        for i0 in range(len(element)):
            i_dof0 = element[i0]
            assert 0 <= i_dof0 < n_dof, f"单元{i_elem}的自由度索引{i_dof0}超出范围"
            lexpr = dyn.get_p2f(i_dof0)
            assert isinstance(lexpr, LinearExpr)

            for i1 in range(len(element)):
                i_dof1 = element[i1]
                assert 0 <= i_dof1 < n_dof, f"单元{i_elem}的自由度索引{i_dof1}超出范围"
                # 刚度矩阵的元素
                try:
                    k = matrix[i0][i1]
                    if i0 == i1:
                        assert k >= 0, f"单元{i_elem}的刚度矩阵元素({i0},{i1})必须非负"
                    lexpr.add(index=i_dof1, weight=-k)
                except Exception as e:
                    print(f"单元{i_elem}的刚度矩阵元素({i0},{i1})出错：{e}")

    # 返回DynSys对象
    return dyn
