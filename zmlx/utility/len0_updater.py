"""热-力耦合：根据渗流模型的温度变化，更新弹簧系统中各弹簧的初始长度（热应变）.

Modified by Claude, 2026-08-12
"""

from zmlx.exts import Vector, SpringSys, Seepage, ElementMap, np


class Len0Updater:
    """热应变更新器。

    备份渗流模型中各 Cell 的初始温度和弹簧系统的初始长度；
    在 ``update`` 时根据当前温度与初始温度的差异计算热应变，
    进而更新各弹簧的初始长度。
    """

    def __init__(self, springsys, seepage, map, ca_t, coeff):
        """初始化热应变更新器。

        构造时立即备份弹簧初始长度和 Cell 初始温度。

        Args:
            springsys: 弹簧系统（SpringSys）。
            seepage: 渗流模型（Seepage）。
            map: Cell 到弹簧的映射（ElementMap）。
            ca_t: 温度属性 ID。
            coeff: 线膨胀系数（约束在 ``1e-8`` 到 ``1e-4`` 之间）。
        """
        self.buffer1 = Vector()
        self.buffer2 = Vector()
        self.springsys = springsys
        self.seepage = seepage
        self.map = map
        self.ca_t = ca_t
        self.coeff = coeff
        self._backup_len0(self.springsys)
        self._backup_T0(self.seepage, self.ca_t)

    def update(self):
        """根据温度变化更新弹簧长度。

        计算热应变：``strain = (T_current - T0) * coeff``，
        然后更新各弹簧的初始长度。
        """
        self._update_strain(self.seepage, self.ca_t, self.coeff)
        self._update_len0(self.springsys, self.map)

    def _backup_len0(self, springsys):
        """备份弹簧系统的初始长度。"""
        assert isinstance(springsys, SpringSys)
        self.len0 = springsys.get_len0().to_numpy()
        self.len1 = np.zeros(shape=self.len0.shape)

    def _backup_T0(self, seepage, ca_t):
        """备份渗流模型各 Cell 的初始温度。"""
        assert isinstance(seepage, Seepage)
        self.T0 = seepage.get_attrs(key='cells', index=ca_t).to_numpy()
        self.strain = np.zeros(shape=self.T0.shape)

    def _update_strain(self, seepage, ca_t, coeff):
        """根据当前温度计算各 Cell 的热应变。"""
        assert isinstance(seepage, Seepage)
        assert 1.0e-8 < coeff < 1.0e-4
        seepage.get_attrs(key='cells', index=ca_t, buffer=self.buffer1)
        assert len(self.buffer1) == len(self.strain)
        self.buffer1.write_numpy(self.strain)
        self.strain -= self.T0
        self.strain *= coeff

    def _update_len0(self, springsys, map):
        """将热应变映射到弹簧并更新初始长度。"""
        assert isinstance(springsys, SpringSys)
        assert isinstance(map, ElementMap)
        self.buffer1.read_numpy(self.strain)
        map.get_values(source=self.buffer1, buffer=self.buffer2,
                       default=0.0)  # 此时buffer2记录了各个弹簧位置的应变(如果没有找到，则应变为0)
        self.buffer2.write_numpy(self.len1)  # 此时len1记录了各个弹簧的应变
        self.len1 *= self.len0  # 此时len1记录了各个弹簧的长度的变化量
        self.len1 += self.len0  # 此时len1为弹簧的变形之后的长度
        self.buffer2.read_numpy(self.len1)
        springsys.set_len0(self.buffer2)  # 应用到弹簧模型
