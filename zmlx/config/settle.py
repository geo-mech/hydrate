"""
支撑剂/颗粒的沉降.
    !!! 后续将移除

2024-4-3
"""
import zmlx.alg.sys as warnings
from zml import Seepage, get_pointer64, np
from zmlx.base.seepage import as_numpy
from zmlx.config.seepage import get_face_sum, get_face_diff, get_face_left, \
    get_face_right

warnings.warn(f'<{__name__}> will be removed after 2025-4-13',
              DeprecationWarning, stacklevel=2)


def get_face_density_diff(model: Seepage, fid0, fid1):
    """
    获得face位置两种流体的密度差
    """
    ca = as_numpy(model).fluids(fid1).den - as_numpy(model).fluids(fid0).den
    fa = np.zeros(shape=model.face_number, dtype=float)
    get_face_sum(
        model, ca=get_pointer64(ca, readonly=True), fa=get_pointer64(fa))
    return fa / 2


def get_face_gra(model: Seepage):
    """
    获取face两侧pos*gravity的差异
    """
    ca = as_numpy(model).cells.g_pos
    fa = np.zeros(shape=model.face_number, dtype=float)
    get_face_diff(
        model, ca=get_pointer64(ca, readonly=True), fa=get_pointer64(fa))
    return fa


def get_face_fv(model: Seepage, fid0, gra):
    """
    获得face位置两种流体的体积的最小值
    """
    ca0 = as_numpy(model).fluids(fid0).vol

    # 左侧的流体0
    fa0 = np.zeros(shape=model.face_number, dtype=float)
    get_face_left(
        model, ca=get_pointer64(ca0, readonly=True), fa=get_pointer64(fa0))

    # 右侧的流体0
    fa1 = np.zeros(shape=model.face_number, dtype=float)
    get_face_right(
        model, ca=get_pointer64(ca0, readonly=True), fa=get_pointer64(fa1))

    # 根据重力，获取上游的流体0体积
    fa = np.zeros(shape=model.face_number, dtype=float)
    mask = gra >= 0
    fa[mask] = fa0[mask]
    mask = gra < 0
    fa[mask] = fa1[mask]
    return fa


def iterate(model: Seepage, dt: float, fid0=None, fid1=None, rate=1.0):
    """
    模拟颗粒在重力作用下的沉降过程.  其中fid0为颗粒的id，fid1为水的id

    其中：
        dt为时间步长；
        fid0和fid1为需要交换的两种流体（fid0为颗粒的id，fid1为水的id）;
        vg用以交换的综合的导流能力；
        vp综合的驱动力；
    """
    if dt <= 1.0e-30:
        return

    # face位置的重力投影
    gra = get_face_gra(model)

    # 基于上面fid0的体积
    cond = get_face_fv(model, fid0, gra) / as_numpy(model).faces.dist

    # 应用重力扩散过程
    if fid0 is not None and fid1 is not None:
        model.diffusion(
            dt * rate, fid0=fid0, fid1=fid1,
            pg=get_pointer64(cond), lg=len(cond),
            ppg=get_pointer64(gra), lpg=len(gra),
            ds_max=0.2)
