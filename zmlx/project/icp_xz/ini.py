def create_ini(perm=None, dist=None, pore_modulus=None, s=None,
               heat_cond=None, z_min=None, z_max=None):
    """
    创建初始场. 注意：
        计算的平面在x-z平面。y方向为垂直于纸面的方向。
    """
    if dist is None:
        dist = 0.2

    if z_min is None:
        z_min = -1e10

    if z_max is None:
        z_max = 1e10

    if perm is None:
        # 绝对渗透率（当考虑上干酪根、焦炭的存在，实际渗透率会远低于这个数值）
        perm = 1.0e-15

    def get_perm(x, y, z):
        if z_min <= z <= z_max:
            return perm
        else:
            return 0

    if pore_modulus is None:
        pore_modulus = 100e6

    if s is None:
        # 默认的初始饱和度(参考赵文智的文章)
        s = {'ch4': 0.08, 'h2o': 0.04, 'lo': 0.08,
             'ho': 0.2, 'kg': 0.6}

    def get_s(x, y, z):
        if z_min <= z <= z_max:
            return s
        else:
            return {'ch4': 1}

    if heat_cond is None:
        heat_cond = 2.0

    def get_fai(x, y, z):
        if z_min <= z <= z_max:
            return 0.3
        else:
            return 0.01

    def get_temperature(x, y, z):   # 温度场，深度增大1m，温度增加0.4
        return 350.0 - z * 0.04

    def get_p(x, y, z):   # 压力场，使用静水压力.
        return 20e6 - z * 1e4

    return {'porosity': get_fai, 'pore_modulus': pore_modulus,
            'p': get_p,
            'temperature': get_temperature,
            'denc': 4e6,
            's': get_s,
            'perm': get_perm,
            'heat_cond': heat_cond,
            'dist': dist  # 决定了流体和固体换热的距离.
            }
