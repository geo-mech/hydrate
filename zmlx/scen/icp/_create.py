from zmlx.exts import Seepage
from zmlx.scen.icp._fluid import create_fludefs
from zmlx.scen.icp._react import create_reactions
from zmlx.tfc import create as create_tfc


def create(fludefs=None, reactions=None, **opts) -> Seepage:
    if fludefs is None:
        fludefs = create_fludefs()

    if reactions is None:
        reactions = create_reactions(temp_max=1000)

    model = create_tfc(fludefs=fludefs, reactions=reactions, **opts)
    return model
