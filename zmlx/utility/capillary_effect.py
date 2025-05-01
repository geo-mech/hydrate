from zml import Interp1, Vector, UintVector, Seepage


class CapillaryEffect:
    """
    定义两种流体之间的毛细管效应。这里假设：
        在同一个Cell内，两种流体之间具有压力差（毛管压力），且压力差和两种流体的体积饱和度相关。对于一种流体，它的饱和度越高，则
        内部压力也越大。
        当相邻的Cell内，流体的饱和度不同的时候。由于高饱和度Cell中流体的压力更高，因此，毛管压力就会驱使着流体在Cell间进行交换。
        如果时间足够长，那么最终的效果，就是各个地方Cell内流体的饱和度最终趋向于相同。
        另外，这里还假设，毛管压力的这种效果，相对于储层的降压等效应，对流体流动的影响是相对小的，因此是一个相对较慢的变量，也就是
        说，在一个时间步dt内，由于毛管效应所交换的流体是比较少的。
    """

    def __init__(self, fid0, fid1, s2p=None):
        """
        建立两种流体之间毛管力效果的模型。其中fid0和fid1定义两种流体的ID。注意，这里只考虑到流体，不考虑各种流体内的组分。因为
        在目前的体系下，我们假设同一流体内的各个组分是可以混溶的。
        s2p为fid0的毛管压力曲线：其自变量x为 v0/(v0+v1)，其中v0和v1分别为fid0和fid1的体积；因变量y为流体fid0相对于fid1的压力
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
        self.s2p_zero = Interp1(x=[0, 1],
                                y=[0, 0.001])  # 用于默认的初始化，定义一个非常小的毛细管压力

    def add_pc(self, cell_ids, s2p):
        if len(cell_ids) > 0:
            self.vpc.append((UintVector(cell_ids), s2p))

    def __call__(self, model, dt):
        """
        利用这里的定义，来更新渗流模型
        """
        assert isinstance(model, Seepage)
        assert dt > 0

        if self.s2p is not None:
            model.get_linear_dpre(fid0=self.fid0, fid1=self.fid1, s2p=self.s2p,
                                  vs0=self.vs0, vk=self.vk, ds=self.ds)
        else:
            # 初始化，避免空值的出现
            # print('init')
            model.get_linear_dpre(fid0=self.fid0, fid1=self.fid1,
                                  s2p=self.s2p_zero, vs0=self.vs0, vk=self.vk,
                                  ds=self.ds)

        if len(self.vpc) > 0:
            for cell_ids, s2p in self.vpc:
                # print(len(cell_ids))
                model.get_linear_dpre(fid0=self.fid0, fid1=self.fid1, s2p=s2p,
                                      vs0=self.vs0, vk=self.vk, ds=self.ds,
                                      cell_ids=cell_ids)

        model.get_cond_for_exchange(fid0=self.fid0, fid1=self.fid1,
                                    buffer=self.vg)
        model.diffusion(dt, fid0=self.fid0, fid1=self.fid1, vs0=self.vs0,
                        vk=self.vk, vg=self.vg, vpg=self.vpg)

    @staticmethod
    def create(fid0, fid1, model, get_idx, *args):
        """
        创建一个毛管压力计算模型，其中fid0和fid1为涉及的两种流体。毛管压力定义为fid0的压力减去fid1的压力。model为创建好的渗流模型（或者Mesh）.
            idx = get_idx(x, y, z)
        是一个函数，该函数返回给定位置所需要采用的毛管压力曲线的ID，注意这个ID从0开始编号.
        后续的所有参数为毛管压力曲线，可以是Interp1类型，也可以给定两个list.
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
        """
        根据文本来创建从饱和度到毛管压力的插值
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
