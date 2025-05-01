from zmlx.react import decomposition
from zmlx.react import vapor
from zmlx.react.inh import add_inh


def create_reactions(temp_max=None):
    """
    创建反应:
        1. 干酪根的裂解
        2. 重油的裂解
        3. 蒸气/水的转化
    其中temp_max为蒸汽反应的时候，设置的温度的最高值.
    """
    result = []

    # 水和蒸汽之间的可逆的反应
    r = vapor.create(vap='steam', wat='h2o',
                     temp_max=temp_max  # 液态水允许的最高的温度
                     )
    result.append(r)

    # kerogen分解
    r = decomposition.create(left='kg',
                             right=[('ho', 0.6),
                                    ('lo', 0.1),
                                    ('h2o', 0.1),
                                    ('ch4', 0.1),
                                    ('char', 0.1)],
                             temp=565.0, heat=161600.0,
                             # From Maryelin 2023-02-23
                             rate=1.0e-8)
    result.append(r)

    # 重油分解
    r = decomposition.create(left='ho',
                             right=[('lo', 0.5),
                                    ('ch4', 0.2),
                                    ('char', 0.3)],
                             temp=603.0, heat=206034.0,
                             # From Maryelin 2023-02-23
                             rate=1.0e-8)
    # 当固体占据的比重达到80%之后，增加裂解温度，从而限制继续分解 (避免所有的孔隙被固体占据)
    add_inh(r, sol='sol', liq=None,
            c=[0, 0.8, 1.0],
            t=[0, 0, 1.0e4], use_vol=True)
    result.append(r)

    # 返回所有的反应
    return result
