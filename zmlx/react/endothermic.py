from zmlx.alg.utils import clamp


def create(left, right, temp, heat, rate=None, fa_t=None, fa_c=None, l2r=True,
           r2l=True, p2t=None,
           t2q=None, inhibitors=None):
    """
    创建吸热的化学反应（以及其逆过程）。其中左侧的物质转化为右侧的物质会吸收热量。温度的升高会促使这种反应的发生.
        left：定义左侧物质的序号和权重
        right：定义右侧物质的序号和权重
        temp：定义反应发生的参考温度
        heat：定义在参考温度下反应发生的时候所消耗的热量 （1kg的左侧物质，转化为1kg的右侧的物质）
        rate：反应的速率（当温度超过平衡温度1度的时候）. 只有当t2q未给定的时候，rate才会有作用.
        fa_t：流体的温度属性
        fa_c：流体的比热属性
        l2r：是否允许左侧的物质转化为右侧的物质
        r2l：是否允许右侧的物质转化为左侧的物质
        p2t：温度压力曲线。定义不同压力下的临界反应温度.
    """
    data = {}

    if fa_t is None:
        fa_t = 'temperature'

    if not isinstance(fa_t, str):
        if fa_t > 9999:
            fa_t = 'temperature'

    if fa_c is None:
        fa_c = 'specific_heat'

    if not isinstance(fa_c, str):
        if fa_c > 9999:
            fa_c = 'specific_heat'

    # 左侧的物质
    components = []
    for kind, weight in left:
        assert weight > 0
        components.append({'kind': kind,
                           'weight': clamp(abs(weight), -1.0, -1.0e-5),
                           'fa_t': fa_t, 'fa_c': fa_c})

    # 右侧的物质
    for kind, weight in right:
        assert weight > 0
        components.append({'kind': kind,
                           'weight': clamp(abs(weight), 1.0e-5, 1.0),
                           'fa_t': fa_t, 'fa_c': fa_c})

    data['components'] = components

    # 参考温度
    assert temp > 0

    # 在参考温度下，反应吸收的热量
    assert heat > 0

    if p2t is not None:
        # 设置温度压力曲线 (如果给定的话)
        data['p2t'] = p2t
    else:
        # 设置分解的温度曲线 <与压力无关的曲线>
        data['p2t'] = ([0.01e6, 100e6], [temp, temp])

    # 设置反应发生的参考温度和在参考温度下的热量
    data['temp'] = temp
    data['heat'] = -heat  # 加上负号非常重要，因为heat为吸收的热量，但是反应的定义需要释放的热量.

    # 定义反应的速率
    if t2q is not None:
        # assert rate is None
        t, q = t2q
        assert len(t) == len(q)
        assert len(t) >= 3
    else:
        # 反应的速率
        assert rate > 0
        dt_max = 1.0e3
        t = [-dt_max, 0, dt_max]
        q = [-rate * dt_max, 0, rate * dt_max]

    for i in range(len(t)):
        if t[i] < 0:
            # 温度低，右侧物质转化为左侧, q <= 0
            if not r2l:
                q[i] = 0
            else:
                q[i] = min(0, q[i])
        if t[i] > 0:
            # 温度高，左侧物质转化为右侧，q >= 0
            if not l2r:
                q[i] = 0
            else:
                q[i] = max(0, q[i])

    data['t2q'] = (t, q)

    # 其它数据
    assert inhibitors is None or isinstance(inhibitors, list)
    data['inhibitors'] = inhibitors if inhibitors is not None else []

    # 完成，返回数据
    return data
