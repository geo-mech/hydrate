from zmlx.react import dissolution

def create_reactions(has_he=True, has_n2=True, others=None):
    """
    创建地热储层中的气体溶解与脱溶反应.
    """
    result = []

    # 1. 氦气 (He) 的动态脱溶与溶解
    if has_he:
        he_dis = dissolution.create(
            sol='he',                # 游离态氦气 (气相产物)
            sol_in_liq='he_sol',     # 溶解态氦气 (液相反应物)
            liq='liq',               # 溶剂 (水)
            ca_sol='he_sol'          # 桥梁：读取 _sol.py 中依据亨利定律计算的溶解度上限
        )
        result.append(he_dis)

    # 2. 氮气 (N2) 的动态脱溶与溶解
    if has_n2:
        n2_dis = dissolution.create(
            sol='n2',                # 游离态氮气 (气相产物)
            sol_in_liq='n2_sol',     # 溶解态氮气 (液相反应物)
            liq='liq',               # 溶剂 (水)
            ca_sol='n2_sol'          # 桥梁：读取 _sol.py 中依据亨利定律计算的溶解度上限
        )
        result.append(n2_dis)

    # 保留外部扩展接口
    if others is not None:
        for item in others:
            result.append(item)

    return result