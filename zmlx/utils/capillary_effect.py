"""两种流体之间的毛细管压力效应（饱和度驱动的压力差导致 Cell 间流体交换）.

Modified by Claude, 2026-08-12
"""

from zmlx.exts import Interp1, Vector, UintVector, Seepage


class CapillaryEffect:
    """两种流体之间的毛细管压力效应模型。

    假设：
    - 在同一 Cell 内，两种流体之间具有压力差（毛管压力），
      且压力差与流体的体积饱和度相关：饱和度越高，内部压力越大。
    - 相邻 Cell 中流体饱和度不同时，高饱和度 Cell 中流体压力更高，
      毛管压力驱使流体在 Cell 间交换。
    - 足够长时间后，各处 Cell 内流体饱和度趋向于相同。
    - 毛管压力效应对流体流动的影响相对于储层降压等效应较小，
      是一个较慢的变量，即在一个时间步 dt 内交换的流体较少。
    """

    def __init__(self, fid0, fid1, s2p=None):
        """建立两种流体之间毛管力效果模型。

        注意：这里只考虑流体，不考虑组分——同一流体内各组分视为可混溶。

        Args:
            fid0: 第一种流体的 ID。
            fid1: 第二种流体的 ID。
            s2p: fid0 的毛管压力曲线。类型支持：
                 - ``Interp1``：直接使用。
                 - ``str``：按 ``create_s2p`` 解析文本。
                 - ``(s, p)`` 元组：两个等长 list，s 递增且 p 递增。
                 - ``None``：不设置全局毛管压力曲线。
                 曲线自变量为 ``v0/(v0+v1)``，因变量为 fid0 相对于 fid1 的压力。
        """
        self.fid0 = fid0
        self.fid1 = fid1

        if s2p is None:
            self.s2p = None
        elif isinstance(s2p, Interp1):
            self.s2p = s2p
        elif isinstance(s2p, str):
            self.s2p = CapillaryEffect.create_s2p(s2p)
        else:
            s, p = s2p
            assert len(s) == len(p) and len(s) >= 2
            for i in range(1, len(s)):
                assert s[i - 1] < s[i]
                assert p[i - 1] < p[i]
            self.s2p = Interp1(x=s, y=p)
        assert self.s2p is None or isinstance(self.s2p, Interp1)

        self.vs0 = Vector()
        self.vk = Vector()
        self.vg = Vector()
        self.vpg = Vector()
        self.vpc = []  # 包含两个部分：Cell的Ids和毛管压力曲线
        self.ds = 0.05
        self.s2p_zero = Interp1(
            x=[0, 1],
            y=[0, 0.001])  # 用于默认的初始化，定义一个非常小的毛细管压力

    def add_pc(self, cell_ids, s2p):
        """为特定 Cell 组添加局部毛管压力曲线。

        Args:
            cell_ids: Cell ID 列表。
            s2p: 该组 Cell 使用的毛管压力曲线（Interp1）。
        """
        if len(cell_ids) > 0:
            self.vpc.append((UintVector(cell_ids), s2p))

    def __call__(self, model, dt):
        """应用毛管压力效应，更新渗流模型。

        Args:
            model: 渗流模型（Seepage）。
            dt: 时间步长 [s]（必须 > 0）。
        """
        assert isinstance(model, Seepage)
        assert dt > 0

        if self.s2p is not None:
            model.get_linear_dpre(
                fid0=self.fid0, fid1=self.fid1, s2p=self.s2p,
                vs0=self.vs0, vk=self.vk, ds=self.ds)
        else:
            # 初始化，避免空值的出现
            # print('init')
            model.get_linear_dpre(
                fid0=self.fid0, fid1=self.fid1,
                s2p=self.s2p_zero, vs0=self.vs0, vk=self.vk,
                ds=self.ds)

        if len(self.vpc) > 0:
            for cell_ids, s2p in self.vpc:
                # print(len(cell_ids))
                model.get_linear_dpre(
                    fid0=self.fid0, fid1=self.fid1, s2p=s2p,
                    vs0=self.vs0, vk=self.vk, ds=self.ds,
                    cell_ids=cell_ids)

        model.get_cond_for_exchange(
            fid0=self.fid0, fid1=self.fid1,
            buffer=self.vg)
        model.diffusion(
            dt, fid0=self.fid0, fid1=self.fid1, vs0=self.vs0,
            vk=self.vk, vg=self.vg, vpg=self.vpg)

    @staticmethod
    def create(fid0, fid1, model, get_idx, *args):
        """创建毛管压力计算模型（按位置分配不同的毛管压力曲线）。

        Args:
            fid0: 第一种流体的 ID。
            fid1: 第二种流体的 ID。
            model: 渗流模型（Seepage）或 Mesh。
            get_idx: 函数 ``idx = get_idx(x, y, z)``，
                     返回给定位置对应的毛管压力曲线 ID（从 0 开始）。
            *args: 毛管压力曲线（``Interp1`` | ``str`` | ``(s, p)`` 元组），
                   与 ``get_idx`` 返回的 ID 一一对应。

        Returns:
            CapillaryEffect: 创建好的毛管压力模型。
        """
        # print('model.cell_number = ', model.cell_number)
        vvi = []
        while len(vvi) < len(args):
            vvi.append([])
        for cell_id in range(model.cell_number):
            idx = int(get_idx(*model.get_cell(cell_id).pos))
            assert 0 <= idx < len(args)
            vvi[idx].append(cell_id)

        cap = CapillaryEffect(fid0, fid1)

        for curve_id in range(len(args)):
            if len(vvi[curve_id]) > 0:
                if isinstance(args[curve_id], Interp1):
                    s2p = args[curve_id]
                elif isinstance(args[curve_id], str):
                    s2p = CapillaryEffect.create_s2p(args[curve_id])
                else:
                    s, p = args[curve_id]
                    assert len(s) == len(p) and len(s) >= 2
                    for i in range(1, len(s)):
                        assert s[i - 1] < s[i]
                        assert p[i - 1] < p[i]
                    s2p = Interp1(x=s, y=p)
                # print(len(vvi[curve_id]), s2p)
                cap.add_pc(vvi[curve_id], s2p)
        return cap

    @staticmethod
    def create_s2p(text):
        """根据文本创建饱和度到毛管压力的插值。

        Args:
            text: 文本内容，每行两个数字（饱和度 压力），空行/短行忽略。

        Returns:
            Interp1: 饱和度 → 毛管压力的一维插值对象。
        """
        vv = [[float(w) for w in line.split()] for line in text.splitlines() if
              len(line) > 2]
        s = [v[0] for v in vv]
        p = [v[1] for v in vv]
        assert len(s) == len(p) and len(s) >= 2
        for i in range(1, len(s)):
            assert s[i - 1] < s[i]
            assert p[i - 1] < p[i]
        return Interp1(x=s, y=p)
