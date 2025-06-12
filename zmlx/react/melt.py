from zmlx.react import endothermic


def create(sol, flu, temp, heat, fa_t=None, fa_c=None, vp=None, vt=None,
           t2q=None, l2r=True, r2l=True):
    """
    创建一个物质融化（或者气化、升华）的反应

    注意：
        返回一个dict，包含了反应的所有的信息。此dict定义的data可以在
        zmlx.react.alg.add_reaction中使用，将反应添加到Seepage中
    """
    if vt is None or vp is None:
        p2t = None
    else:
        p2t = [vp, vt]
    return endothermic.create(
        left=[(sol, 1), ],
        right=[(flu, 1), ],
        temp=temp,
        heat=heat,
        rate=1.0,
        fa_t=fa_t,
        fa_c=fa_c,
        l2r=l2r, r2l=r2l, p2t=p2t, t2q=t2q)
