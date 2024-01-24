from zml import *

core = DllCore(dll=load_cdll(name='heavy_oil.dll',
                             first=os.path.dirname(__file__)))

core.use(None, 'vdisc3_modify_perm', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)


def modify_perm(vdisc3, seepage, fa_k, ca_fp, da_pc, da_k):
    """
    对于圆盘控制的face，检查流体压力是否超过了临界值。如果流体压力超过了临界值，则相当于裂缝打开，则增加face渗透率；
    其中：
        fa_k:  定义face位置的渗透率
        ca_fp：定义Cell的流体压力
        da_pc：定义圆盘的临界流体压力
        da_k： 定义圆盘的渗透率

    注意：
        这个函数在运行的过程中，除了修改渗透率之外，还会修改圆盘的face_ids这个属性，这样的涉及其实是很不好的.
        后续将移除.
    """
    warnings.warn('Disc3.face_ids is modified when modify_perm. function remove after 2024-9-21',
                  DeprecationWarning)
    assert isinstance(seepage, Seepage)
    core.vdisc3_modify_perm(vdisc3.handle, seepage.handle, fa_k, ca_fp, da_pc, da_k)


class Disc3(HasHandle):
    """
    三维的圆盘
    """
    core.use(c_void_p, 'new_disc3')
    core.use(None, 'del_disc3', c_void_p)

    def __init__(self, coord=None, radi=None, handle=None):
        super(Disc3, self).__init__(handle, core.new_disc3, core.del_disc3)
        if handle is None:
            if coord is not None:
                self.coord = coord
            if radi is not None:
                self.radi = radi

    core.use(c_void_p, 'disc3_get_coord', c_void_p)
    core.use(None, 'disc3_set_coord', c_void_p, c_void_p)

    @property
    def coord(self):
        """
        圆盘所在的坐标系
        """
        return Coord3(handle=core.disc3_get_coord(self.handle))

    @coord.setter
    def coord(self, value):
        """
        圆盘所在的坐标系
        """
        assert isinstance(value, Coord3)
        core.disc3_set_coord(self.handle, value.handle)

    core.use(None, 'disc3_set_radi', c_void_p, c_double)
    core.use(c_double, 'disc3_get_radi', c_void_p)

    @property
    def radi(self):
        """
        圆盘的半径 [m]
        """
        return core.disc3_get_radi(self.handle)

    @radi.setter
    def radi(self, value):
        """
        圆盘的半径 [m]
        """
        core.disc3_set_radi(self.handle, value)

    core.use(None, 'disc3_create', c_void_p, c_double, c_double, c_double, c_double, c_double, c_double)

    @staticmethod
    def create(x, y, z, direction, angle, r, buffer=None):
        """
        创建一个圆盘
        """
        if not isinstance(buffer, Disc3):
            buffer = Disc3()
        core.disc3_create(buffer.handle, x, y, z, direction, angle, r)
        return buffer

    core.use(c_bool, 'disc3_get_intersection', c_void_p, c_void_p, c_void_p, c_void_p)
    core.use(c_bool, 'disc3_get_intersection_with_segment', c_void_p, c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double)
    core.use(c_bool, 'disc3_get_intersection_with_xoy', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_intersection(self, other=None, p1=None, p2=None, buffer=None, coord=None):
        """
        返回交线/交点
        """
        if isinstance(coord, Coord3):
            # 返回和给定坐标系的xoy平面的交线
            if not isinstance(p1, Array3):
                p1 = Array3()
            if not isinstance(p2, Array3):
                p2 = Array3()
            if core.disc3_get_intersection_with_xoy(self.handle, coord.handle, p1.handle, p2.handle):
                return p1, p2
            else:
                return
        if isinstance(other, Disc3):
            # 返回和另一个圆盘的交线
            if not isinstance(p1, Array3):
                p1 = Array3()
            if not isinstance(p2, Array3):
                p2 = Array3()
            if core.disc3_get_intersection(self.handle, other.handle, p1.handle, p2.handle):
                return p1, p2
        else:
            # 返回和线段的交点
            if not isinstance(buffer, Array3):
                buffer = Array3()
            if core.disc3_get_intersection_with_segment(self.handle, buffer.handle, p1[0], p1[1], p1[2], p2[0], p2[1],
                                                        p2[2]):
                return buffer

    core.use(None, 'disc3_get_lat_inds', c_void_p, c_void_p, c_void_p)

    def get_lat_inds(self, lat, buffer=None):
        """
        将这个圆盘投射到给定的格子上，返回这个圆盘所占据的格子的序号.
        """
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        assert isinstance(lat, Lattice3)
        core.disc3_get_lat_inds(self.handle, buffer.handle, lat.handle)
        return buffer

    core.use(None, 'disc3_create_mesh', c_void_p, c_void_p, c_size_t)

    def create_mesh(self, count=20, buffer=None):
        """
        生成用于显示该圆盘的三角形网格
        """
        if not isinstance(buffer, Mesh3):
            buffer = Mesh3()
        core.disc3_create_mesh(self.handle, buffer.handle, count)
        return buffer

    core.use(c_void_p, 'disc3_get_cell_ids', c_void_p)

    @property
    def cell_ids(self):
        """
        在渗流计算的时候，此圆盘经过所有的Cell的Id. 在Disc3中存储这些ID不是好的设计，后续此属性会移除.
        """
        warnings.warn('Disc3.cell_ids will be removed after 2024-10-13', DeprecationWarning)
        return UintVector(handle=core.disc3_get_cell_ids(self.handle))

    core.use(c_void_p, 'disc3_get_face_ids', c_void_p)

    @property
    def face_ids(self):
        """
        在渗流计算的时候，此圆盘经过所有的Cell的Id. 在Disc3中存储这些ID不是好的设计，后续此属性会移除.
        """
        warnings.warn('Disc3.face_ids will be removed after 2024-10-13', DeprecationWarning)
        return UintVector(handle=core.disc3_get_face_ids(self.handle))

    core.use(c_double, 'disc3_get_attr', c_void_p, c_size_t)
    core.use(None, 'disc3_set_attr', c_void_p, c_size_t, c_double)

    def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
        """
        第index个自定义属性。
        当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
        """
        if index is None:
            return default_val
        value = core.disc3_get_attr(self.handle, index)
        if min <= value <= max:
            return value
        else:
            return default_val

    def set_attr(self, index, value):
        """
        第index个自定义属性。
        当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
        """
        if index is None:
            return self
        if value is None:
            value = 1.0e200
        core.disc3_set_attr(self.handle, index, value)
        return self

    core.use(None, 'disc3_add_scale', c_void_p, c_double)

    def add_scale(self, value):
        """
        在空间的位置、大小都等比例放大一定的倍数
        """
        core.disc3_add_scale(self.handle, value)

    core.use(None, 'disc3_copy', c_void_p, c_void_p)

    def copy(self, other):
        """
        从另外一个Disc3拷贝数据
        """
        assert isinstance(other, Disc3)
        core.disc3_copy(self.handle, other.handle)

    @staticmethod
    def get_copy(disc3, buffer=None):
        """
        返回当前Disc3的一个拷贝
        """
        if not isinstance(buffer, Disc3):
            buffer = Disc3()
        buffer.copy(disc3)
        return buffer


class Disc3Vec(HasHandle):
    """
    一个由三维圆盘组成的数组
    """
    core.use(c_void_p, 'new_vdisc3')
    core.use(None, 'del_vdisc3', c_void_p)

    def __init__(self, path=None, handle=None):
        super(Disc3Vec, self).__init__(handle, core.new_vdisc3, core.del_vdisc3)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return f'zml.Disc3Vec(size={len(self)})'

    core.use(None, 'vdisc3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.vdisc3_save(self.handle, make_c_char_p(path))

    core.use(None, 'vdisc3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.vdisc3_load(self.handle, make_c_char_p(path))

    core.use(None, 'vdisc3_push_back', c_void_p, c_void_p)

    def append(self, disc):
        """
        添加一个圆盘
        """
        assert isinstance(disc, Disc3)
        core.vdisc3_push_back(self.handle, disc.handle)

    core.use(c_size_t, 'vdisc3_size', c_void_p)

    def __len__(self):
        """
        返回数量
        """
        return core.vdisc3_size(self.handle)

    core.use(c_void_p, 'vdisc3_get', c_void_p, c_size_t)

    def __getitem__(self, index):
        """
        返回index位置的数据
        """
        if index < len(self):
            return Disc3(handle=core.vdisc3_get(self.handle, index))

    core.use(None, 'vdisc3_create_mesh', c_void_p, c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def create_mesh(self, count=20, da=99999999, na=99999999, fa=99999999, buffer=None):
        """
        生成用于显示该圆盘的三角形网格
        da:
            对于各个disc，尝试输出的自定义属性

        na:
            对于各个node，添加自定义属性，用以标识这个node所在的圆盘的序号

        fa:
            对于各个face，添加自定义属性，用以标识这个face所在的圆盘的序号
        """
        if not isinstance(buffer, Mesh3):
            buffer = Mesh3()
        core.vdisc3_create_mesh(self.handle, buffer.handle, count, da, na, fa)
        return buffer


if __name__ == '__main__':
    print(core.time_compile)
