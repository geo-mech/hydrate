"""生成可重复的不规则分叉裂缝，并计算裂缝带对原面渗透/导热系数的影响。

这是等效高渗带几何，不是新的求解器；不模拟压裂扩展、酸化反应或真实开度。
"""

import math
import random


def make_fractures(extent, *, seed, count, vertical_ratio):
    """生成由井周向外延伸、长短不一且含分叉的折线网络。

    Args:
        extent: 中心线离井中心最远距离m；零返回空网络。
        seed: 固定随机种子；不改变全局随机数状态。
        count: 主裂缝条数，每隔一条附加一条分叉。
        vertical_ratio: 竖向压缩比，0到1，使裂缝总体水平展布。

    Returns:
        list: 每条折线的[x,z]坐标点列表；井轴沿y方向。

    Raises:
        ValueError: 尺度、数量或比例无效。
    """
    if extent < 0 or count < 3 or not 0 < vertical_ratio <= 1:
        raise ValueError("裂缝延伸范围须非负、主裂缝至少3条、竖向比例须在(0,1]")
    if extent == 0:
        return []
    rng = random.Random(seed)
    paths = []
    for i in range(count):
        angle = 2*math.pi*i/count + rng.uniform(-0.15, 0.15)
        length = rng.uniform(0.7, 1.0)
        path = [[0.0, 0.0]]
        for fraction in (0.12, 0.30, 0.52, 0.75, 1.0):
            direction = angle + rng.uniform(-0.20, 0.20)
            path.append([length*fraction*math.cos(direction),
                         vertical_ratio*length*fraction*math.sin(direction)])
        paths.append(path)
        if i % 2 == 0:
            x, z = path[3]
            side_angle = angle + rng.choice((-1, 1))*rng.uniform(0.45, 0.85)
            fork_length = length*rng.uniform(0.22, 0.38)
            fork = [[x, z]]
            for fraction in (0.45, 1.0):
                direction = side_angle + rng.uniform(-0.15, 0.15)
                fork.append([x + fork_length*fraction*math.cos(direction),
                             z + vertical_ratio*fork_length*fraction*math.sin(direction)])
            paths.append(fork)
    scale = extent/max(math.hypot(x, z) for path in paths for x, z in path)
    return [[[scale*x, scale*z] for x, z in path] for path in paths]


def _linear_interval(value, slope, low, high):
    """求线性函数落在给定范围且t在[0,1]内的区间。

    Args:
        value, slope: value+slope*t的系数。
        low, high: 允许值范围。

    Returns:
        tuple: t区间；无交集返回None。
    """
    if abs(slope) < 1e-14:
        return (0.0, 1.0) if low <= value <= high else None
    a, b = sorted(((low-value)/slope, (high-value)/slope))
    lo, hi = max(0.0, a), min(1.0, b)
    return (lo, hi) if hi > lo else None


def _circle_interval(x, z, dx, dz, cx, cz, radius):
    """求单元连线进入裂缝端部圆形圆帽的参数区间。

    Args:
        x, z: 连线起点m。
        dx, dz: 连线向量m，不能为零向量。
        cx, cz: 圆心m。
        radius: 半带宽m。

    Returns:
        tuple: [0,1]内交段；无交集返回None。
    """
    x, z = x-cx, z-cz
    a, b = dx*dx+dz*dz, 2*(x*dx+z*dz)
    disc = b*b-4*a*(x*x+z*z-radius*radius)
    if disc <= 0:
        return None
    root = math.sqrt(disc)
    lo, hi = max(0.0, (-b-root)/(2*a)), min(1.0, (-b+root)/(2*a))
    return (lo, hi) if hi > lo else None


class FractureBands:
    """不规则折线的有限宽度并集，重叠位置只计算一次。"""

    def __init__(self, paths, width):
        """预计算各裂缝段方向及包围盒。

        Args:
            paths: make_fractures生成的折线列表。
            width: 等效高渗带全宽m，必须为正。

        Raises:
            ValueError: 带宽非正。
        """
        if width <= 0:
            raise ValueError("等效裂缝带宽度必须为正")
        self.paths, self.half_width = paths, width/2
        self.segments = []
        for path in paths:
            for (x, z), (bx, bz) in zip(path[:-1], path[1:]):
                length = math.hypot(bx-x, bz-z)
                if length > 1e-12:
                    self.segments.append((x, z, bx, bz, (bx-x)/length, (bz-z)/length, length))

    def fraction(self, p0, p1):
        """求单元中心连线穿过高渗裂缝带并集的长度比例。

        Args:
            p0, p1: 不同三维单元中心坐标m，取其中x、z。

        Returns:
            float: [0,1]内比例，供原tfc面系数调和平均。
        """
        x, z, dx, dz = p0[0], p0[2], p1[0]-p0[0], p1[2]-p0[2]
        width, intervals = self.half_width, []
        xmin, xmax, zmin, zmax = min(x, x+dx), max(x, x+dx), min(z, z+dz), max(z, z+dz)
        for ax, az, bx, bz, ux, uz, length in self.segments:
            if (xmax < min(ax, bx)-width or xmin > max(ax, bx)+width
                    or zmax < min(az, bz)-width or zmin > max(az, bz)+width):
                continue
            along = _linear_interval((x-ax)*ux+(z-az)*uz, dx*ux+dz*uz, 0, length)
            across = _linear_interval(-(x-ax)*uz+(z-az)*ux, -dx*uz+dz*ux, -width, width)
            if along is not None and across is not None:
                lo, hi = max(along[0], across[0]), min(along[1], across[1])
                if hi > lo:
                    intervals.append((lo, hi))
            for cx, cz in ((ax, az), (bx, bz)):
                interval = _circle_interval(x, z, dx, dz, cx, cz, width)
                if interval is not None:
                    intervals.append(interval)
        total, right = 0.0, 0.0
        for lo, hi in sorted(intervals):
            total += max(0.0, hi-max(right, lo))
            right = max(right, hi)
        return min(1.0, total)

    def mask(self, x, z):
        """返回各单元中心是否落在裂缝带内的掩膜，用于保存和核查几何。

        Args:
            x, z: 一维单元中心坐标数组m。

        Returns:
            ndarray: shape=(len(x),len(z))的布尔掩膜。
        """
        import numpy as np
        xx, zz = np.meshgrid(x, z, indexing="ij")
        mask = np.zeros(xx.shape, dtype=bool)
        for ax, az, bx, bz, ux, uz, length in self.segments:
            along = np.clip((xx-ax)*ux+(zz-az)*uz, 0, length)
            mask |= (xx-ax-along*ux)**2+(zz-az-along*uz)**2 <= self.half_width**2
        return mask
