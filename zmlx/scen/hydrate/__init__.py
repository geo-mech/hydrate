"""
水合物相关计算模型.
"""
from zmlx.scen.hydrate._cap import create_caps
from zmlx.scen.hydrate._config import Config, ConfigV2
from zmlx.scen.hydrate._create import create
from zmlx.scen.hydrate._fluid import create_fludefs
from zmlx.scen.hydrate._ini import create_t_ini, create_p_ini, create_denc_ini, create_fai_ini
from zmlx.scen.hydrate._opt import create_opts
from zmlx.scen.hydrate._react import create_reactions
from zmlx.scen.hydrate._show import show_2d, show_2d_v2
from zmlx.scen.hydrate._solve import solve

create_kwargs = create_opts
