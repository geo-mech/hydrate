
class FdyConfig(HasHandle):
    class CellKeys:
        def __init__(self, handle):
            self.handle = handle

        core.use(None, 'fdy2_set_key_fp', c_void_p, c_size_t)
        core.use(c_size_t, 'fdy2_get_key_fp', c_void_p)

        @property
        def fp(self):
            return core.fdy2_get_key_fp(self.handle)

        @fp.setter
        def fp(self, value):
            core.fdy2_set_key_fp(self.handle, value)

    class FaceKeys:
        def __init__(self, handle):
            self.handle = handle

        core.use(None, 'fdy2_set_key_v0', c_void_p, c_size_t)
        core.use(c_size_t, 'fdy2_get_key_v0', c_void_p)

        @property
        def v0(self):
            return core.fdy2_get_key_v0(self.handle)

        @v0.setter
        def v0(self, value):
            core.fdy2_set_key_v0(self.handle, value)

        core.use(None, 'fdy2_set_key_v1', c_void_p, c_size_t)
        core.use(c_size_t, 'fdy2_get_key_v1', c_void_p)

        @property
        def v1(self):
            return core.fdy2_get_key_v1(self.handle)

        @v1.setter
        def v1(self, value):
            core.fdy2_set_key_v1(self.handle, value)

        core.use(None, 'fdy2_set_key_v2', c_void_p, c_size_t)
        core.use(c_size_t, 'fdy2_get_key_v2', c_void_p)

        @property
        def v2(self):
            return core.fdy2_get_key_v2(self.handle)

        @v2.setter
        def v2(self, value):
            core.fdy2_set_key_v2(self.handle, value)

    class Cell:
        def __init__(self, handle):
            self.handle = handle

    class Face:
        def __init__(self, handle):
            self.handle = handle

        core.use(None, 'fdy2_face_set_dir', c_void_p, c_size_t, c_double)
        core.use(c_double, 'fdy2_face_get_dir', c_void_p, c_size_t)

        @property
        def dir(self):
            a = core.fdy2_get_sdir(self.handle, 0)
            b = core.fdy2_get_sdir(self.handle, 1)
            c = core.fdy2_get_sdir(self.handle, 2)
            return a, b, c

        @dir.setter
        def dir(self, value):
            assert len(value) == 3
            for i in range(3):
                core.fdy2_face_set_dir(self.handle, i, value[i])

        core.use(None, 'fdy2_face_set_vol', c_void_p, c_double)
        core.use(c_double, 'fdy2_face_get_vol', c_void_p)

        @property
        def vol(self):
            return core.fdy2_face_get_vol(self.handle)

        @vol.setter
        def vol(self, value):
            core.fdy2_face_set_vol(self.handle, value)

        core.use(c_void_p, 'fdy2_face_get_p2f', c_void_p)

        @property
        def p2f(self):
            return FdyConfig.Pre2Force(core.fdy2_face_get_p2f(self.handle))

    class Shear:
        def __init__(self, handle):
            self.handle = handle

        core.use(None, 'fdy2_shear_set_lnk', c_void_p, c_size_t, c_size_t)
        core.use(c_size_t, 'fdy2_shear_get_lnk0', c_void_p)
        core.use(c_size_t, 'fdy2_shear_get_lnk1', c_void_p)

        @property
        def lnk(self):
            i0 = core.fdy2_shear_get_lnk0(self.handle)
            i1 = core.fdy2_shear_get_lnk1(self.handle)
            return i0, i1

        @lnk.setter
        def lnk(self, value):
            core.fdy2_shear_set_lnk(self.handle, value[0], value[1])

        core.use(None, 'fdy2_shear_set_area_vs_dist', c_void_p, c_double)
        core.use(c_double, 'fdy2_shear_get_area_vs_dist', c_void_p)

        @property
        def area_vs_dist(self):
            return core.fdy2_shear_get_area_vs_dist(self.handle)

        @area_vs_dist.setter
        def area_vs_dist(self, value):
            core.fdy2_shear_set_area_vs_dist(self.handle, value)

    class Pre2Force:
        def __init__(self, handle):
            self.handle = handle

        core.use(None, 'fdy2_p2f_add_ik', c_void_p, c_size_t,
                 c_double, c_double, c_double)

        def add(self, cell_id, k0, k1, k2):
            core.fdy2_p2f_add_ik(self.handle, cell_id, k0, k1, k2)

        core.use(None, 'fdy2_p2f_clear', c_void_p)

        def clear(self):
            core.fdy2_p2f_clear(self.handle)

    core.use(c_void_p, 'new_fdy2')
    core.use(None, 'del_fdy2', c_void_p)

    def __init__(self, path=None, handle=None):
        super(FdyConfig, self).__init__(handle, core.new_fdy2, core.del_fdy2)
        if handle is None:
            if path is not None:
                self.load(path)

    def __str__(self):
        return f'zml.FluDyn(handle = {self.handle})'

    core.use(None, 'fdy2_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.fdy2_save(self.handle, make_c_char_p(path))

    core.use(None, 'fdy2_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.fdy2_load(self.handle, make_c_char_p(path))

    @property
    def cell_keys(self):
        return FdyConfig.CellKeys(self.handle)

    @property
    def face_keys(self):
        return FdyConfig.FaceKeys(self.handle)

    core.use(c_size_t, 'fdy2_get_cell_n', c_void_p)

    @property
    def cell_number(self):
        return core.fdy2_get_cell_n(self.handle)

    core.use(c_void_p, 'fdy2_get_cell', c_void_p, c_size_t)

    def get_cell(self, index):
        if index < self.cell_number:
            return FdyConfig.Cell(core.fdy2_get_cell(self.handle, index))

    core.use(c_size_t, 'fdy2_add_cell', c_void_p)

    def add_cell(self):
        index = core.fdy2_add_cell()
        return self.get_cell(index)

    core.use(c_size_t, 'fdy2_get_face_n', c_void_p)

    @property
    def face_number(self):
        return core.fdy2_get_face_n(self.handle)

    core.use(c_void_p, 'fdy2_get_face', c_void_p, c_size_t)

    def get_face(self, index):
        if index < self.face_number:
            return FdyConfig.Face(core.fdy2_get_face(self.handle, index))

    core.use(c_size_t, 'fdy2_add_face', c_void_p)

    def add_face(self):
        index = core.fdy2_add_face()
        return self.get_face(index)

    core.use(c_size_t, 'fdy2_get_shear_n', c_void_p)

    @property
    def shear_number(self):
        return core.fdy2_get_shear_n(self.handle)

    core.use(c_void_p, 'fdy2_get_shear', c_void_p, c_size_t)

    def get_shear(self, index):
        if index < self.shear_number:
            return FdyConfig.Shear(core.fdy2_get_shear(self.handle, index))

    core.use(c_size_t, 'fdy2_add_shear', c_void_p)

    def add_shear(self):
        index = core.fdy2_add_shear()
        return self.get_shear(index)

    core.use(c_size_t, 'fdy2_iterate', c_void_p, c_void_p, c_double,
             c_double, c_double,
             c_size_t, c_double)

    def iterate(self, seepage_model, dt, precision=1.0e-3, relax_factor=0.9, nloop_max=0, ratio_max=0.98):
        assert isinstance(seepage_model, Seepage)
        return core.fdy2_iterate(self.handle, seepage_model.handle,
                                 dt, precision, relax_factor, nloop_max, ratio_max)

