from typing import Optional, List, Any

from zmlx.exts import FluDef
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.solution import create_solute


def create_aqueous(name: str = 'liq', *, h2o: Optional[FluDef] = None, solutes: Optional[List[List[Any]]] = None,
                   **others):
    """
    创建水溶液定义. 其中h2o是水的定义。在此基础上，添加各种溶质。每一个溶质都是一个List或者Tuple，格式为：
        name(名字), c(基准浓度), den_times(基准浓度下密度相对于纯水的比例), vis_times(基准浓度下粘度相对于纯水的比例)
    """
    if h2o is None:
        h2o = create_h2o()

    liq = FluDef(name=name)
    liq.add_component(h2o, name='h2o' if len(h2o.name) == 0 else h2o.name)

    if solutes is not None:
        for solute in solutes:
            assert len(solute) > 0
            name, opt = solute[0], solute[1:]
            sol = create_solute(
                solvent=h2o,
                c=opt[0] if 0 < len(opt) else 0.1,
                den_times=opt[1] if 1 < len(opt) else 1.0,
                vis_times=opt[2] if 2 < len(opt) else 1.0
            )
            liq.add_component(sol, name=name)

    for name, opt in others.items():
        sol = create_solute(
            solvent=h2o,
            c=opt[0] if 0 < len(opt) else 0.1,
            den_times=opt[1] if 1 < len(opt) else 1.0,
            vis_times=opt[2] if 2 < len(opt) else 1.0
        )
        liq.add_component(sol, name=name)
    return liq


def test_1():
    liq = create_aqueous(
        solutes=[
            ['co2'],
            ['Ca+'],
        ],
        he=[0.1, 1.1, 1.0],
        h2=[]
    )
    for c in liq.components:
        print(c)


if __name__ == '__main__':
    test_1()
