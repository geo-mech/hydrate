import zmlx.alg.sys as warnings


def create_caps(
        inh_diff=None,
        co2_diff=None,
        ch4_diff=None,
        co2_cap=None,
        ch4_cap=None,
        others=None):
    """
    创建扩散过程
    """
    result = []

    # 盐度的扩散
    if inh_diff is not None:
        warnings.warn(
            'inh_diff已弃用. 后续，请使用 zmlx.config.diffusion的相关功能',
            DeprecationWarning,
            stacklevel=2
        )
        assert inh_diff >= 0
        cap = dict(
            fid0='inh', fid1='h2o',
            get_idx=lambda x, y, z: 0,
            data=[[[0, 1], [0, inh_diff]], ])
        result.append(cap)

    # 溶解co2的扩散
    if co2_diff is not None:
        warnings.warn(
            'co2_diff已弃用. 后续，请使用 zmlx.config.diffusion的相关功能',
            DeprecationWarning,
            stacklevel=2
        )
        assert co2_diff >= 0
        cap = dict(
            fid0='co2_in_liq', fid1='h2o',
            get_idx=lambda x, y, z: 0,
            data=[[[0, 1], [0, co2_diff]], ])
        result.append(cap)

    # 溶解ch4的扩散
    if ch4_diff is not None:
        warnings.warn(
            'ch4_diff已弃用. 后续，请使用 zmlx.config.diffusion的相关功能',
            DeprecationWarning,
            stacklevel=2
        )
        assert ch4_diff >= 0
        cap = dict(
            fid0='ch4_in_liq', fid1='h2o',
            get_idx=lambda x, y, z: 0,
            data=[[[0, 1], [0, ch4_diff]], ])
        result.append(cap)

    # 自由co2的扩散（毛管压力驱动下）
    if co2_cap is not None:
        assert co2_cap >= 0
        cap = dict(
            fid0='co2', fid1='liq',
            get_idx=lambda x, y, z: 0,
            data=[[[0, 1], [0, co2_cap]], ])
        result.append(cap)

    # 自由ch4的扩散（毛管压力驱动下）
    if ch4_cap is not None:
        assert ch4_cap >= 0
        cap = dict(
            fid0='ch4', fid1='liq',
            get_idx=lambda x, y, z: 0,
            data=[[[0, 1], [0, ch4_cap]], ])
        result.append(cap)

    if others is not None:
        for item in others:
            result.append(item)

    # 返回结果.
    return result
