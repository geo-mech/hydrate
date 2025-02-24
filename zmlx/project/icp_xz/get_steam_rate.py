def get_steam_rate(power, temp):
    """
    给定加热的功率，计算生成蒸汽的速率(kg/s)
    """
    assert temp >= 373

    # 生成1kg的蒸汽需要消耗的热量
    energy = 2596000.0 + (temp - 373.0) * 1850.0

    # 得到了生成蒸汽的质量速率
    rate = power / energy

    return rate


if __name__ == '__main__':
    print(get_steam_rate(power=1e3, temp=800))

