from zmlx.react import dissolution


def create_reactions():
    """
    创建反应.
    """
    he_dis = dissolution.create(
        sol='he', sol_in_liq='he_sol',
        liq='liq', ca_sol='he_sol'
    )
    n2_dis = dissolution.create(
        sol='n2', sol_in_liq='n2_sol',
        liq='liq', ca_sol='n2_sol'
    )
    return [he_dis, n2_dis]
