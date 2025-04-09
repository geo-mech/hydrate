from zml import Vector, SpringSys, Seepage, ElementMap, np


class Len0Updater:

    def __init__(self, springsys, seepage, map, ca_t, coeff):
        """
        初始化模型
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
        """
        通过温度的变化，来更新各个弹簧的长度
        """
        self._update_strain(self.seepage, self.ca_t, self.coeff)
        self._update_len0(self.springsys, self.map)

    def _backup_len0(self, springsys):
        """
        备份弹簧系统各个弹簧的初始的长度。接下来，当温度发生改变的时候，
        将根据这个初始长度，以及温度的变化量，来计算新的弹簧长度
        """
        assert isinstance(springsys, SpringSys)
        self.len0 = springsys.get_len0().to_numpy()
        self.len1 = np.zeros(shape=self.len0.shape)

    def _backup_T0(self, seepage, ca_t):
        """
        备份渗流模型各个Cell的温度，和弹簧的初始长度对应
        """
        assert isinstance(seepage, Seepage)
        self.T0 = seepage.get_attrs(key='cells', index=ca_t).to_numpy()
        self.strain = np.zeros(shape=self.T0.shape)

    def _update_strain(self, seepage, ca_t, coeff):
        """
        通过当前的温度，计算各个Cell温度的变化量，进而计算应变
        """
        assert isinstance(seepage, Seepage)
        assert 1.0e-8 < coeff < 1.0e-4
        seepage.get_attrs(key='cells', index=ca_t, buffer=self.buffer1)
        assert len(self.buffer1) == len(self.strain)
        self.buffer1.write_numpy(self.strain)
        self.strain -= self.T0
        self.strain *= coeff

    def _update_len0(self, springsys, map):
        """
        更新弹簧的长度
        """
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
