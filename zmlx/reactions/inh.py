"""抑制剂反应.

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn

def create_inh(
        sol, liq, c=None, t=None, *, use_vol=False,
        c2t=None, c2q=None, exp=None, exp_r=None):
    """
    创建反应的抑制剂数据
    """
    if c is not None and t is not None:
        c2t = c, t
        warn(
            'The arguments c and t will be removed after 2026-5-30, please use c2t instead',
            DeprecationWarning, stacklevel=2)

    return dict(
        sol=sol, liq=liq, use_vol=use_vol, c2t=c2t, c2q=c2q,
        exp=exp, exp_r=exp_r)


def add_inh(r: dict, *args, **kwargs):
    r['inhibitors'].append(
        create_inh(*args, **kwargs)
    )
