from zml import *


def update_p_max(network, fa_id, fa_p_max, seepage, fixed_n, layer_n):
    """
    更新裂缝网络各个单元所对应的Cell中的流体压力的最大值 （这个最大值后续将用于计算裂缝的扩展）.
    其中：
        fa_id为裂缝单元对应的seepage中的Cell的Id；
        fa_p_max存储返回的结果，为最大压力
        fixed_n为seepage中固定的cell的数量
        layer_n为seepage中Cell的层数
    注意：
        此函数的调用需要保证seepage的拓扑结构是最新的，因此，最好在 update_seepage_topology函数之后执行
    """
    assert isinstance(seepage, Seepage)
    assert isinstance(network, FractureNetwork2)
    assert fixed_n <= seepage.cell_number
    assert layer_n >= 1

    active_n = seepage.cell_number - fixed_n
    assert active_n % layer_n == 0
    layer_cell_n = active_n // layer_n
    assert isinstance(layer_cell_n, int)  # 必须确保是int，否则后面传入dll的时候会出错
    assert layer_cell_n * layer_n + fixed_n == seepage.cell_number

    for frac in network.get_fractures():
        cell_id0 = frac.get_attr(fa_id)
        assert 0 <= cell_id0 < seepage.cell_number
        cell_id0 = int(cell_id0)
        fp_max = 0
        for layer_i in range(layer_n):
            cell_id = fixed_n + layer_i * layer_cell_n + cell_id0
            assert fixed_n <= cell_id < seepage.cell_number
            cell = seepage.get_cell(cell_id)
            fp = cell.v2p(cell.fluid_vol)
            fp_max = max(fp, fp_max)
        frac.set_attr(fa_p_max, fp_max)

