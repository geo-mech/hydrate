"""
第二阶段：溶解气体被动运移专用 create

本文件用于 He_sol / n2_sol / ch4_sol 的水相被动运移测试。

注意：
1. 不启用亨利定律；
2. 不启用脱溶反应；
3. 不调用 update_he_sol；
4. 不调用 update_n2_sol；
5. 不调用 update_ch4_sol；
6. 只把 he_sol / n2_sol / ch4_sol 当作水相被动组分。
"""

from zmlx.exts import Seepage
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.solution import create_solute
from zmlx.tfc import create as create_tfc


def _vapor():
    """
    水蒸气，占位。
    第二阶段不考虑气相生成。
    """
    return Seepage.FluDef(name='vapor', den=30.0, vis=1.0e-5)


def _he():
    """
    气相 He，占位。
    第二阶段不发生 He 脱溶，因此该气相物性暂不控制结果。
    """
    return Seepage.FluDef(name='he', den=27.0, vis=2.2e-5)


def _n2():
    """
    气相 N2，占位。
    第二阶段不发生 N2 脱溶，因此该气相物性暂不控制结果。
    """
    return Seepage.FluDef(name='n2', den=195.0, vis=2.1e-5)


def _ch4():
    """
    气相 CH4，占位。
    第二阶段不发生 CH4 脱溶，因此该气相物性暂不控制结果。

    后续如果进入脱溶 / 气相运移阶段，应替换为更严格的
    压力-温度相关 CH4 物性。
    """
    return Seepage.FluDef(name='ch4', den=120.0, vis=1.5e-5)


def _h2o():
    """
    水相。
    """
    return create_h2o(name='h2o')


def _he_sol(h2o):
    """
    作为水相溶质的 He。
    这里不代表亨利定律溶解度，只是创建一个水相被动组分。
    """
    return create_solute(
        solvent=h2o,
        c=0.01,
        den_times=1.0,
        vis_times=1.0,
        name='he_sol'
    )


def _n2_sol(h2o):
    """
    作为水相溶质的 N2。
    这里不代表亨利定律溶解度，只是创建一个水相被动组分。
    """
    return create_solute(
        solvent=h2o,
        c=0.01,
        den_times=1.0,
        vis_times=1.0,
        name='n2_sol'
    )


def _ch4_sol(h2o):
    """
    作为水相溶质的 CH4。
    这里不代表亨利定律溶解度，只是创建一个水相被动组分。
    """
    return create_solute(
        solvent=h2o,
        c=0.01,
        den_times=1.0,
        vis_times=1.0,
        name='ch4_sol'
    )


def create_fludefs():
    """
    创建第二阶段被动运移所需流体定义。

    组分编号大致为：
    气相 gas:
        [0, 0] vapor
        [0, 1] he
        [0, 2] n2
        [0, 3] ch4

    液相 liq:
        [1, 0] h2o
        [1, 1] he_sol
        [1, 2] n2_sol
        [1, 3] ch4_sol
    """

    gas = Seepage.FluDef.create(
        name='gas',
        defs=[
            _vapor(),
            _he(),
            _n2(),
            _ch4()
        ]
    )

    h2o = _h2o()

    liq = Seepage.FluDef.create(
        name='liq',
        defs=[
            h2o,
            _he_sol(h2o),
            _n2_sol(h2o),
            _ch4_sol(h2o)
        ]
    )

    return [gas, liq]


def create(**opts) -> Seepage:
    """
    创建第二阶段被动运移模型。
    """

    default_opts = dict(
        fludefs=create_fludefs(),
        reactions=[]
    )

    default_opts.update(opts)

    model = create_tfc(**default_opts)

    return model


def _test():
    """
    测试流体定义是否包含 he_sol / n2_sol / ch4_sol。
    """
    from zmlx.tfc import cell_keys

    model = create()
    ca = cell_keys(model)

    print(model)
    print("he_sol  key =", ca.he_sol)
    print("n2_sol  key =", ca.n2_sol)

    try:
        print("ch4_sol key =", ca.ch4_sol)
    except Exception as e:
        print("无法读取 ch4_sol key，请检查 create_fludefs 中是否成功定义 ch4_sol")
        print(e)


if __name__ == '__main__':
    _test()