from zml import FractureNetwork, Seepage
from zmlx.alg.utils import clamp


def update_cond(
        flow: Seepage, network: FractureNetwork,
        *,
        aperture_max=0.01,
        g_times_max=10.0,
        relax_factor=0.1,
        exp=3.0):
    """更新flow中所有的Face的导流系数。

    Args:
        flow (Seepage): 渗流模型对象，会更新其所有的Face的cond
        network (FractureNetwork): 裂缝网络对象，会读取其裂缝的开度
        aperture_max (float, optional): 最大的开度值，用于计算g_times
        g_times_max (float, optional): 最大的g_times值，用于计算cond
        relax_factor (float, optional): 控制cond的变化量的系数
        exp (float, optional): 开度指数（默认3.0对应立方定律）

    Returns:
        None
    """
    assert 0.0 < relax_factor <= 0.5, \
        f'The range of relax_factor is (0, 0.5]. relax_factor = {relax_factor}'
    assert 1.0 <= g_times_max <= 100.0, \
        f'The range of g_times_max is (1, 100]. g_times_max = {g_times_max}'

    # 基础的导流系数
    g1 = flow.get_attr(index='face_g1')
    g2 = flow.get_attr(index='face_g2')

    fracture_g_times = [
        1.0 + clamp(max(-fracture.dn, 0.0) / aperture_max,
                    0, 1.0) ** exp * (
                g_times_max - 1)
        for fracture in network.fractures]

    # 代表方向
    fa_dir = flow.get_face_key('direction')
    assert fa_dir is not None, f'The face attribute "direction" is not found'

    fracture_n = network.fracture_number
    for face in flow.faces:
        assert isinstance(face, Seepage.Face)
        face_dir = round(face.get_attr(fa_dir))
        assert face_dir == 1 or face_dir == 2
        i0, i1 = face.get_cell(0).index, face.get_cell(1).index
        i0 = i0 % fracture_n
        i1 = i1 % fracture_n
        assert i0 < len(fracture_g_times)
        assert i1 < len(fracture_g_times)
        g_times = (fracture_g_times[i0] + fracture_g_times[i1]) / 2
        if face_dir == 1:
            g0 = g1
        else:
            g0 = g2
        d_cond = g0 * g_times - face.cond
        d_cond *= relax_factor  # 限制cond的变化量
        face.cond = clamp(face.cond + d_cond, g0, g0 * g_times_max)
