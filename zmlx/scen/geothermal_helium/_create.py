from zmlx.exts import Seepage
from zmlx.scen.geothermal_helium._fluid import create_fludefs
from zmlx.scen.geothermal_helium._react import create_reactions
from zmlx.scen.geothermal_helium._sol import update_n2_sol, update_he_sol
from zmlx.tfc import create as create_tfc, cell_keys


def create(**opts) -> Seepage:
    """
    创建计算模型.
    """
    default_opts = dict(
        fludefs=create_fludefs(),
        reactions=create_reactions()
    )
    default_opts.update(opts)
    model = create_tfc(**default_opts)

    # 设置初始的溶解度属性
    update_he_sol(model)
    update_n2_sol(model)

    return model


def _test():
    model = create()
    print(model)
    ca = cell_keys(model)
    print(ca.n2_sol)
    print(ca.he_sol)


if __name__ == '__main__':
    _test()
