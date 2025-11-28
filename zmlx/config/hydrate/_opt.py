import zmlx.alg.sys as warnings
from zmlx.config.hydrate._cap import create_caps
from zmlx.config.hydrate._fluid import create_fludefs
from zmlx.config.hydrate._react import create_reactions
from zmlx.kr.base import create_krf


def create_opts(
        has_co2=False,
        has_steam=False,
        has_inh=False,
        has_ch4_in_liq=False,
        has_co2_in_liq=False,
        inh_diff=None,
        ch4_diff=None,
        co2_diff=None,
        co2_cap=None,
        ch4_cap=None,
        support_ch4_hyd_diss=True,
        support_ch4_hyd_form=True,
        gr=None,
        h2o_density=None,
        co2_def=None,
        ch4_def=None,
        h2o_def=None,
        inh_def=None,
        co2_sol_data=None,  # 溶解co2的定义
        ch4_sol_data=None,  # 溶解ch4的定义
        inh_sol_data=None,  # 溶解inh的定义
        gravity=None,
        dt_max=None,
        sol_dt=None,
        **kwargs):
    """
    返回用于seepage.create的参数列表
        当给定co2的时候，将使用给定的定义. (since 2024-1-10)
    """
    if has_co2_in_liq:  # 此时，必须要求存在co2
        has_co2 = True

    fludefs = create_fludefs(
        has_co2=has_co2,
        has_steam=has_steam,
        has_inh=has_inh,
        has_ch4_in_liq=has_ch4_in_liq,
        has_co2_in_liq=has_co2_in_liq,
        h2o_density=h2o_density,
        co2_def=co2_def,
        ch4_def=ch4_def,
        h2o_def=h2o_def,
        inh_def=inh_def,
        other_gas=None,
        other_liq=None,
        other_sol=None,
        co2_sol_data=co2_sol_data,
        ch4_sol_data=ch4_sol_data,
        inh_sol_data=inh_sol_data,
    )

    reactions = create_reactions(
        support_ch4_hyd_diss=support_ch4_hyd_diss,
        support_ch4_hyd_form=support_ch4_hyd_form,
        has_inh=has_inh,
        has_co2=has_co2,
        has_steam=has_steam,
        has_ch4_in_liq=has_ch4_in_liq,
        has_co2_in_liq=has_co2_in_liq,
        sol_dt=sol_dt,
    )

    # 修改部分参数，确保协调.
    if not has_inh:
        inh_diff = None
    if not has_ch4_in_liq:
        ch4_diff = None
    if not has_co2_in_liq:
        co2_diff = None
    if not has_co2:
        co2_cap = None

    if ch4_diff is not None:
        warnings.warn(
            'ch4_diff已弃用. 后续，请使用 zmlx.config.diffusion的相关功能',
            DeprecationWarning,
            stacklevel=2
        )

    if inh_diff is not None:
        warnings.warn(
            'inh_diff已弃用. 后续，请使用 zmlx.config.diffusion的相关功能',
            DeprecationWarning,
            stacklevel=2
        )

    if co2_diff is not None:
        warnings.warn(
            'co2_diff已弃用. 后续，请使用 zmlx.config.diffusion的相关功能',
            DeprecationWarning,
            stacklevel=2
        )

    caps = create_caps(
        ch4_diff=ch4_diff,
        inh_diff=inh_diff,
        co2_diff=co2_diff,
        co2_cap=co2_cap,
        ch4_cap=ch4_cap
    )

    if dt_max is None:
        dt_max = 3600 * 24

    if gr is None:
        gr = create_krf(as_interp=True)

    if gravity is None:
        gravity = [0, -10, 0]

    # 返回结果.
    return dict(
        dt_max=dt_max,
        fludefs=fludefs,
        reactions=reactions,
        caps=caps,
        gr=gr,
        gravity=gravity,
        has_solid=True,
        **kwargs)
