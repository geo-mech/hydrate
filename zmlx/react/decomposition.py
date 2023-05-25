from zmlx.react import endothermic


def create(index, iweights, temp, heat, rate, fa_t, fa_c):
    """
    创建物质吸热分解的反应<不可逆的>. 其中index为待分解的物质，iweights为右侧物质的序号和权重，temp为分解的温度，heat为分解1kg左侧物质的耗能，
    rate是温度超过分解温度1度的时候，对于左侧1kg的物质，1s内能否反应的物质的质量；
    fa_t和fa_c为物质的属性ID，定义物质的温度和比热;
    """
    return endothermic.create(left=[(index, 1), ],
                              right=iweights,
                              temp=temp, heat=heat, rate=rate, fa_t=fa_t, fa_c=fa_c,
                              l2r=True, r2l=False, p2t=None, t2q=None)
