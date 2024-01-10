from zml import *

core = DllCore(dll=load_cdll(name='frac.dll' if is_windows else 'frac.so.1',
                             first=os.path.dirname(__file__)))


class DDMSolution2(HasHandle):
    """
    二维DDM的基本解
    """
    core.use(c_void_p, 'new_ddm_sol2')
    core.use(None, 'del_ddm_sol2', c_void_p)

    def __init__(self, handle=None):
        super(DDMSolution2, self).__init__(handle, core.new_ddm_sol2, core.del_ddm_sol2)

    core.use(None, 'ddm_sol2_save', c_void_p, c_char_p)
    core.use(None, 'ddm_sol2_load', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.ddm_sol2_save(self.handle, make_c_char_p(path))

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.ddm_sol2_load(self.handle, make_c_char_p(path))

    core.use(None, 'ddm_sol2_set_alpha', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_alpha', c_void_p)

    @property
    def alpha(self):
        return core.ddm_sol2_get_alpha(self.handle)

    @alpha.setter
    def alpha(self, value):
        core.ddm_sol2_set_alpha(self.handle, value)

    core.use(None, 'ddm_sol2_set_beta', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_beta', c_void_p)

    @property
    def beta(self):
        return core.ddm_sol2_get_beta(self.handle)

    @beta.setter
    def beta(self, value):
        core.ddm_sol2_set_beta(self.handle, value)

    core.use(None, 'ddm_sol2_set_shear_modulus', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_shear_modulus', c_void_p)

    @property
    def shear_modulus(self):
        return core.ddm_sol2_get_shear_modulus(self.handle)

    @shear_modulus.setter
    def shear_modulus(self, value):
        core.ddm_sol2_set_shear_modulus(self.handle, value)

    core.use(None, 'ddm_sol2_set_poisson_ratio', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_poisson_ratio', c_void_p)

    @property
    def poisson_ratio(self):
        return core.ddm_sol2_get_poisson_ratio(self.handle)

    @poisson_ratio.setter
    def poisson_ratio(self, value):
        core.ddm_sol2_set_poisson_ratio(self.handle, value)

    core.use(None, 'ddm_sol2_set_adjust_coeff', c_void_p, c_double)
    core.use(c_double, 'ddm_sol2_get_adjust_coeff', c_void_p)

    @property
    def adjust_coeff(self):
        return core.ddm_sol2_get_adjust_coeff(self.handle)

    @adjust_coeff.setter
    def adjust_coeff(self, value):
        core.ddm_sol2_set_adjust_coeff(self.handle, value)

    core.use(None, 'ddm_sol2_get_induced', c_void_p, c_void_p,
             c_double, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double,
             c_double, c_double, c_double)

    def get_induced(self, pos, fracture, ds, dn, height):
        """
        返回一个裂缝单元的诱导应力
        """
        assert len(fracture) == 4
        stress = Tensor2()
        if len(pos) == 2:
            core.ddm_sol2_get_induced(self.handle, stress.handle, *pos, *pos,
                                      *fracture, ds, dn, height)
        else:
            assert len(pos) == 4
            core.ddm_sol2_get_induced(self.handle, stress.handle, *pos,
                                      *fracture, ds, dn, height)
        return stress


class Fracture2:
    """
    二维裂缝单元
    """

    def __init__(self, handle):
        self.handle = handle

    core.use(c_double, 'frac2_get_pos', c_void_p, c_size_t)

    @property
    def pos(self):
        """
        返回一个长度为4的list，表示裂缝的位置。格式为 [x0, y0, x1, y1]。其中(x0, y0)为
        裂缝第一个端点的位置，(x1, y1)第二个端点的位置坐标;
        """
        return [core.frac2_get_pos(self.handle, i) for i in range(4)]

    core.use(c_size_t, 'frac2_get_uid', c_void_p)

    @property
    def uid(self):
        """
        裂缝的全局ID。在程序启动之后，裂缝的ID将会是唯一的，并且是递增的。因此uid的数值越大，则表明裂缝创建得越晚。 另外，在裂缝扩展
        的过程种，也可以用这个uid来判断，哪些裂缝是新的。
        """
        return core.frac2_get_uid(self.handle)

    core.use(None, 'frac2_set_ds', c_void_p, c_double)
    core.use(c_double, 'frac2_get_ds', c_void_p)

    @property
    def ds(self):
        """
        切向位移间断
        """
        return core.frac2_get_ds(self.handle)

    @ds.setter
    def ds(self, value):
        assert -1e6 < value < 1e6
        core.frac2_set_ds(self.handle, value)

    core.use(None, 'frac2_set_dn', c_void_p, c_double)
    core.use(c_double, 'frac2_get_dn', c_void_p)

    @property
    def dn(self):
        """
        法向位移间断
        """
        return core.frac2_get_dn(self.handle)

    @dn.setter
    def dn(self, value):
        assert -1e6 < value < 1.0
        core.frac2_set_dn(self.handle, value)

    core.use(None, 'frac2_set_h', c_void_p, c_double)
    core.use(c_double, 'frac2_get_h', c_void_p)

    @property
    def h(self):
        """
        裂缝的高度
        """
        return core.frac2_get_h(self.handle)

    @h.setter
    def h(self, value):
        assert -1.0e-2 < value < 1e100
        core.frac2_set_h(self.handle, value)

    core.use(None, 'frac2_set_fric', c_void_p, c_double)
    core.use(c_double, 'frac2_get_fric', c_void_p)

    @property
    def fric(self):
        """
        摩擦系数
        """
        return core.frac2_get_fric(self.handle)

    @fric.setter
    def fric(self, value):
        assert 0 < value < 100
        core.frac2_set_fric(self.handle, value)

    core.use(None, 'frac2_set_p0', c_void_p, c_double)
    core.use(c_double, 'frac2_get_p0', c_void_p)

    @property
    def p0(self):
        """
        当dn=0的时候，内部流体的压力（内部流体压力随着裂缝开度的增加<即随着dn降低>而降低）
        """
        return core.frac2_get_p0(self.handle)

    @p0.setter
    def p0(self, value):
        """
        当dn=0的时候，内部流体的压力（内部流体压力随着裂缝开度的增加<即随着dn降低>而降低）
        """
        core.frac2_set_p0(self.handle, value)

    core.use(None, 'frac2_set_k', c_void_p, c_double)
    core.use(c_double, 'frac2_get_k', c_void_p)

    @property
    def k(self):
        """
        dn增大1(缝宽减小1)的时候的压力增加量(>=0)
        """
        return core.frac2_get_k(self.handle)

    @k.setter
    def k(self, value):
        """
        dn增大1(缝宽减小1)的时候的压力增加量(>=0)
        """
        assert 0 <= value
        core.frac2_set_k(self.handle, value)

    core.use(c_double, 'frac2_get_attr', c_void_p, c_size_t)
    core.use(None, 'frac2_set_attr', c_void_p, c_size_t, c_double)

    def get_attr(self, index, min=-1.0e100, max=1.0e100, default_val=None):
        """
        第index个自定义属性
        当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
        """
        if index is None:
            return default_val
        if index < 0:
            if index == -1:
                return self.ds
            if index == -2:
                return self.dn
            if index == -3:
                return self.h
            if index == -4:
                return self.fric
            if index == -5:
                return self.p0
            if index == -6:
                return self.k
            if index == -11:  # 宽度
                return -self.dn
            return default_val
        value = core.frac2_get_attr(self.handle, index)
        if min <= value <= max:
            return value
        else:
            return default_val

    def set_attr(self, index, value):
        """
        第index个自定义属性
        当index个属性不存在时，默认为无穷大的一个值(1.0e100以上的浮点数)
        """
        if value is None:
            value = 1.0e200
        if index is None:
            return self
        if index < 0:
            if index == -1:
                self.ds = value
                return self
            if index == -2:
                self.dn = value
                return self
            if index == -3:
                self.h = value
                return self
            if index == -4:
                self.fric = value
                return self
            if index == -5:
                self.p0 = value
                return self
            if index == -6:
                self.k = value
                return self
            else:
                return self
        else:
            core.frac2_set_attr(self.handle, index, value)
            return self


class FractureNetwork2(HasHandle):
    """
    二维裂缝网络
    """
    core.use(c_void_p, 'new_fnet2')
    core.use(None, 'del_fnet2', c_void_p)

    def __init__(self, handle=None):
        super(FractureNetwork2, self).__init__(handle, core.new_fnet2, core.del_fnet2)

    def __str__(self):
        return f'zml.FractureNetwork2(handle = {self.handle}, vtx_n = {self.vtx_n}, frac_n = {self.frac_n})'

    core.use(None, 'fnet2_save', c_void_p, c_char_p)
    core.use(None, 'fnet2_load', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.fnet2_save(self.handle, make_c_char_p(path))

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.fnet2_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'fnet2_get_frac_n', c_void_p)

    @property
    def frac_n(self):
        return core.fnet2_get_frac_n(self.handle)

    core.use(c_size_t, 'fnet2_get_vtx_n', c_void_p)

    @property
    def vtx_n(self):
        return core.fnet2_get_vtx_n(self.handle)

    core.use(None, 'fnet2_add', c_void_p, c_double, c_double, c_double, c_double, c_double)

    def add_fracture(self, pos, lave):
        """
        添加裂缝
        """
        assert len(pos) == 4
        core.fnet2_add(self.handle, *pos, lave)

    core.use(None, 'fnet2_get_fractures', c_void_p, c_void_p)

    def get_fractures(self, buffer=None):
        """
        返回所有的裂缝单元
        """
        if not isinstance(buffer, PtrVector):
            buffer = PtrVector()
        core.fnet2_get_fractures(self.handle, buffer.handle)
        return [Fracture2(handle=buffer[i]) for i in range(buffer.size)]

    core.use(None, 'fnet2_adjust', c_void_p, c_double, c_double)

    def adjust(self, lave, angle_min=0.4):
        """
        调整裂缝格局，尽量避免病态的情况出现
        """
        core.fnet2_adjust(self.handle, lave, angle_min)

    core.use(c_size_t, 'fnet2_create_branch', c_void_p, c_void_p, c_void_p, c_double)
    core.use(c_size_t, 'fnet2_extend_tip', c_void_p, c_void_p, c_void_p,
             c_double, c_double, c_double, c_double)
    core.use(c_size_t, 'fnet2_extend_tip3', c_void_p,
             c_void_p, c_double, c_double, c_double, c_double, c_double, c_double, c_double,
             c_void_p,
             c_double, c_double, c_double, c_double)

    def extend(self, kic=None, sol2=None, lave=None, dn_min=1.0e-7, lex=0.3, dangle_max=10.0,
               has_branch=True, z=0, left=None, right=None):
        """
        尝试扩展裂缝，并返回扩展的数量.
            lex:   扩展的长度与lave的比值
        注意：
            在裂缝扩展的过程中，裂缝单元的数量可能并不会发生改变. 在扩展的时候，会首先将尖端的单元拉长。只有
            当这个尖端的裂缝的长度被拉长到不得不分割的时候，才会被分成两个裂缝单元。在这个尖端被分割的时候，
            裂缝的数据(包括所有的属性)，将会被分割之后的两个单元所共同继承. 因此，当裂缝单元通过fa_id属性
            来定义裂缝单元对应的Cell的id的时候，在裂缝扩展的时候，将可能会出现，两个单元所对应的cell为同
            一个的情况(在 update_seepage_topology 的时候，会考虑到这个问题，并自动对相应的Cell进行拆分).
        """
        count = 0
        if has_branch:
            assert isinstance(kic, Tensor2)
            assert isinstance(sol2, DDMSolution2)
            assert lave is not None
            count += core.fnet2_create_branch(self.handle, kic.handle, sol2.handle, lave)
        if 0.01 < lex < 0.99:
            assert isinstance(sol2, DDMSolution2)
            assert lave is not None
            if isinstance(kic, Tensor2):
                assert isinstance(kic, Tensor2)
                count += core.fnet2_extend_tip(self.handle, kic.handle, sol2.handle,
                                               dn_min, lave, lex, dangle_max)
            else:
                assert isinstance(kic, Tensor3Matrix3)
                assert left is not None
                assert right is not None
                count += core.fnet2_extend_tip3(self.handle, kic.handle,
                                                left[0], left[1], left[2], right[0], right[1], right[2],
                                                z,
                                                sol2.handle, dn_min, lave, lex, dangle_max)
        return count

    core.use(None, 'fnet2_get_induced', c_void_p, c_void_p, c_void_p,
             c_double, c_double, c_double, c_double)

    def get_induced(self, pos, sol2):
        """
        返回所有裂缝的诱导应力
        """
        assert isinstance(sol2, DDMSolution2)
        stress = Tensor2()
        if len(pos) == 2:
            core.fnet2_get_induced(self.handle, stress.handle, sol2.handle, *pos, *pos)
        else:
            assert len(pos) == 4
            core.fnet2_get_induced(self.handle, stress.handle, sol2.handle, *pos)
        return stress

    core.use(None, 'fnet2_update_h_by_layers', c_void_p, c_void_p, c_size_t, c_double, c_double)

    def update_h_by_layers(self, layers, fa_id, layer_h, w_min):
        """
        利用分层的数据来更新各个裂缝单元的高度;
        """
        if not isinstance(layers, PtrVector):
            layers = PtrVector.from_objects(layers)
        core.fnet2_update_h_by_layers(self.handle, layers.handle, fa_id, layer_h, w_min)

    core.use(None, 'fnet2_copy_attr', c_void_p, c_size_t, c_size_t)

    def copy_attr(self, idest, isrc):
        """
        将ID为isrc的裂缝单元属性复制到idest位置
        """
        core.fnet2_copy_attr(self.handle, idest, isrc)

    core.use(c_double, 'fnet2_get_dn_min', c_void_p)
    core.use(c_double, 'fnet2_get_dn_max', c_void_p)

    @property
    def dn_min(self):
        return core.fnet2_get_dn_min(self.handle)

    @property
    def dn_max(self):
        return core.fnet2_get_dn_max(self.handle)

    core.use(c_double, 'fnet2_get_ds_min', c_void_p)
    core.use(c_double, 'fnet2_get_ds_max', c_void_p)

    @property
    def ds_min(self):
        return core.fnet2_get_ds_min(self.handle)

    @property
    def ds_max(self):
        return core.fnet2_get_ds_max(self.handle)

    core.use(None, 'fnet2_update_dist2tip', c_void_p, c_size_t, c_size_t)

    def update_dist2tip(self, fa_dist, va_dist):
        """
        更新各个裂缝距离裂缝尖端的距离，并存储在属性fa_dist中。va_dist为各个节点距离裂缝尖端的距离，仅仅作为辅助计算的临时变量
        """
        core.fnet2_update_dist2tip(self.handle, fa_dist, va_dist)

    core.use(None, 'fnet2_update_cluster', c_void_p, c_size_t)

    def update_cluster(self, fa_cid):
        """
        更新cluster (将裂缝单元划分为相互孤立的cluster)
        """
        core.fnet2_update_cluster(self.handle, fa_cid)

    core.use(None, 'fnet2_update_fh', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    def update_fh(self, fa_h, fa_cid, fa_dist, h_vs_l):
        """
        假定裂缝的形状为一个椭圆，从而根据裂缝的长度来更新裂缝的高度
        """
        core.fnet2_update_fh(self.handle, fa_h, fa_cid, fa_dist, h_vs_l)

    core.use(None, 'fnet2_update_boundary', c_void_p, c_void_p, c_size_t, c_double)
    core.use(None, 'fnet2_update_boundary_by_layers', c_void_p, c_void_p, c_size_t)

    def update_boundary(self, seepage, fa_id, fh=None):
        """
        在DDM中，流体是作为固体计算的边界。此函数根据此刻的流体情况来更新固体计算的边界条件。
        其中:
            seepage 可以为一个或者多个Seepage类。当Seepage为多个时，其指针存储在PtrVector中;
            fa_id 为裂缝单元中存储的流体Cell的ID。

        注意：
            对于各个裂缝单元，将首先计算它对应的Cell(用fa_id指定)中的流体的体积，然后计算裂缝的长度，并使用
            给定的fh或者裂缝内存储的裂缝高度来计算裂缝的面积，进而计算流体的厚度。这个厚度就是对裂缝开度的一个
            非常硬的约束，也是后续计算裂缝的dn和ds的时候的边界条件.
        """
        if isinstance(seepage, Seepage):
            if fh is None:
                fh = -1  # Now, using the fracture height defined in fracture.
            core.fnet2_update_boundary(self.handle, seepage.handle, fa_id, fh)
        else:
            if not isinstance(seepage, PtrVector):
                seepage = PtrVector.from_objects(seepage)
            core.fnet2_update_boundary_by_layers(self.handle, seepage.handle, fa_id)

    core.use(None, 'fnet2_mark_tips', c_void_p, c_size_t)

    def mark_tips(self, fa_is_tip):
        """
        标记位于尖端的裂缝单元。对于尖端的单元，将自定义属性fa_is_tip的值设置为1，对于其它的单元，fa_is_tip的值设置为0.
            since 2023-9-14
        """
        core.fnet2_mark_tips(self.handle, fa_is_tip)

    core.use(None, 'fnet2_mark_length', c_void_p, c_size_t)

    def mark_length(self, fa_length):
        """
        标记出裂缝单元的长度
            since 2023-9-14
        """
        core.fnet2_mark_length(self.handle, fa_length)


class InfManager2(HasHandle):
    """
    二维裂缝的管理（建立应力影响矩阵）
    注意：
        这是一个临时变量，因此没有提供save/load函数。在调用update_matrix之后，矩阵会自动创建.
    """
    core.use(c_void_p, 'new_fmanager2')
    core.use(None, 'del_fmanager2', c_void_p)

    def __init__(self, handle=None):
        super(InfManager2, self).__init__(handle, core.new_fmanager2, core.del_fmanager2)

    core.use(None, 'fmanager2_update1', c_void_p, c_void_p, c_void_p, c_void_p, c_double)
    core.use(None, 'fmanager2_update2', c_void_p, c_void_p, c_void_p, c_void_p, c_double, c_double)
    core.use(None, 'fmanager2_update3', c_void_p, c_void_p, c_void_p, c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double)

    def update_matrix(self, network, sol, stress, dist, z=0, left=None, right=None):
        """
        更新应力影响矩阵. 其中：
            dist为应力影响的范围. 当两个裂缝之间的距离大于dist的时候，则它们之间不会产生
            实时的应力影响。也就是说，会利用它们此刻的开度和剪切来计算应力，而这部分应力在
            后续不会随着它们开度的变化而变化。
        """
        assert isinstance(network, FractureNetwork2)
        assert isinstance(sol, DDMSolution2)
        if isinstance(stress, Tensor2):
            core.fmanager2_update1(self.handle, network.handle, sol.handle, stress.handle, dist)
        elif isinstance(stress, Tensor3Interp3):
            core.fmanager2_update2(self.handle, network.handle, sol.handle, stress.handle, z, dist)
        else:
            assert isinstance(stress, Tensor3Matrix3)
            assert left is not None
            assert right is not None
            core.fmanager2_update3(self.handle, network.handle, sol.handle,
                                   stress.handle,
                                   left[0], left[1], left[2],
                                   right[0], right[1], right[2],
                                   z, dist)

    core.use(c_size_t, 'fmanager2_update_disp', c_void_p, c_double, c_double, c_size_t, c_double)

    def update_disp(self, gradw_max=0, err_max=0.1, iter_max=10000, ratio_max=0.99):
        """
        更新裂缝单元的位移(dn和ds)
        """
        return core.fmanager2_update_disp(self.handle, gradw_max, err_max, iter_max, ratio_max)

    core.use(None, 'fmanager2_update_boundary', c_void_p, c_void_p, c_size_t, c_double)
    core.use(None, 'fmanager2_update_boundary_by_layers', c_void_p, c_void_p, c_size_t)

    def update_boundary(self, seepage, fa_id, fh=None):
        """
        在DDM中，流体是作为固体计算的边界。此函数根据此刻的流体情况来更新固体计算的边界条件。
        其中:
            seepage 可以为一个或者多个Seepage类。当Seepage为多个时，其指针存储在PtrVector中;
            fa_id 为裂缝单元中存储的流体Cell的ID。

        注意：
            对于各个裂缝单元，将首先计算它对应的Cell(用fa_id指定)中的流体的体积，然后计算裂缝的长度，并使用
            给定的fh或者裂缝内存储的裂缝高度来计算裂缝的面积，进而计算流体的厚度。这个厚度就是对裂缝开度的一个
            非常硬的约束，也是后续计算裂缝的dn和ds的时候的边界条件.
        """
        warnings.warn('please use FractureNetwork2.update_boundary instead', DeprecationWarning)
        if isinstance(seepage, Seepage):
            if fh is None:
                fh = -1  # Now, using the fracture height defined in fracture.
            core.fmanager2_update_boundary(self.handle, seepage.handle, fa_id, fh)
        else:
            if not isinstance(seepage, PtrVector):
                seepage = PtrVector.from_objects(seepage)
            core.fmanager2_update_boundary_by_layers(self.handle, seepage.handle, fa_id)


class ExHistory(HasHandle):
    core.use(c_void_p, 'new_exhistory')
    core.use(None, 'del_exhistory', c_void_p)

    def __init__(self, path=None, handle=None):
        super(ExHistory, self).__init__(handle, core.new_exhistory, core.del_exhistory)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'exhistory_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.exhistory_save(self.handle, make_c_char_p(path))

    core.use(None, 'exhistory_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.exhistory_load(self.handle, make_c_char_p(path))

    core.use(None, 'exhistory_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'exhistory_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.exhistory_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.exhistory_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'exhistory_record', c_void_p, c_double, c_size_t)

    def record(self, dt, n_extend):
        """
        记录扩展的过程
        :param dt: 采用的时间步长
        :param n_extend: 扩展的数量
        """
        core.exhistory_record(self.handle, dt, n_extend)

    core.use(c_double, 'exhistory_get_best_dt', c_void_p, c_double)

    def get_best_dt(self, prob):
        """
        返回给定扩展概率下面最佳的时间步长
        :param prob: 扩展的概率. 如果希望每10步裂缝可以发生一次扩展，则prob应该设置为0.1
        """
        return core.exhistory_get_best_dt(self.handle, prob)


class Hf2Alg:
    core.use(None, 'hf2_alg_leakoff', c_void_p, c_size_t, c_size_t, c_size_t,
             c_double,
             c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def leak_off(seepage, fluid_id, dt, ca_vlk, ca_vis_lk, ca_s, ca_fai, ca_k, ca_pp):
        """
        计算流体的滤失. 其中fluid_id为即将滤失的流体的ID, dt为时间步长. ca_vlk为已经滤失的流体的体积； ca_vis_lk为已经滤失的流体的粘性；
        ca_s为滤失面积；ca_fai为滤失孔隙度；ca_k为滤失渗透率；ca_pp为远端的孔隙压力；
        """
        assert isinstance(seepage, Seepage)
        core.hf2_alg_leakoff(seepage.handle, *parse_fid3(fluid_id), dt, ca_vlk, ca_vis_lk, ca_s, ca_fai, ca_k, ca_pp)

    core.use(None, 'hf2_alg_update_seepage_topology', c_void_p, c_void_p, c_size_t,
             c_size_t, c_size_t, c_size_t)

    @staticmethod
    def update_seepage_topology(seepage, network, fa_id, fa_new=None, cell_new=None, face_new=None):
        """
        建立和裂缝对应的流动模型.
            其中：
            fa_id为裂缝的自定义属性的ID，用以存储这个裂缝单元对应的Seepage中的Cell的ID.
            fa_new为裂缝的自定义属性的ID，当这个属性非0时，表示这是一个新的裂缝单元（新添加的，或者被新分隔的，均被视为新的单元）
            cell_new和face_new是seepage中cell和face的属性ID，用于表示这是否为新的cell或者face
            注意：
            1. 这里的seepage需要被这个裂缝系统所独占。即，这里建立的目标，是裂缝单元和seepage中的Cell一对一。但是，为了确保存储在
            fracture中的Cell的id不发生变化，这里不允许删除seepage中的Cell。当裂缝变少的时候，多余的Cell将会被标记成为孤立的Cell，
            不和其它的Cell产生流体的联通。
            2. 在创建seepage的时候，会尽量保证Cell中的流体和pore不发生变化。如果有Cell被两个裂缝所共有，那么，将会把Cell中的数据按照
            两条裂缝的长度的比例分配给两个fracture单元(所以，大部分的属性应该会得到保留).
            3. 在此函数执行之后，对于每一个裂缝单元，都将有一个Cell来对应，且每一个Cell最多只和一个fracture对应。
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork2)
        core.hf2_alg_update_seepage_topology(seepage.handle, network.handle, fa_id,
                                             fa_new if fa_new is not None else 99999999,
                                             cell_new if cell_new is not None else 99999999,
                                             face_new if face_new is not None else 99999999
                                             )

    core.use(c_bool, 'hf2_alg_seepage_topology_expired', c_void_p, c_size_t)

    @staticmethod
    def seepage_topology_expired(network, fa_id):
        """
        判断裂缝对应的渗流是否已经过期（1、两个fracture共用一个cell，2、存在尚未设置cell的fracture）
        since 2023-9-24
        """
        assert isinstance(network, FractureNetwork2)
        return core.hf2_alg_seepage_topology_expired(network.handle, fa_id)

    core.use(None, 'hf2_alg_update_seepage_cell_pos', c_void_p, c_void_p, c_void_p, c_size_t)

    @staticmethod
    def update_seepage_cell_pos(seepage, network, coord, fa_id):
        """
        根据各个裂缝单元中心点的坐标来更新各个Cell的位置；
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork2)
        assert isinstance(coord, Coord3)
        core.hf2_alg_update_seepage_cell_pos(seepage.handle, network.handle, coord.handle, fa_id)

    core.use(None, 'hf2_alg_update_cond0', c_void_p, c_void_p, c_double, c_size_t, c_double)
    core.use(None, 'hf2_alg_update_cond1', c_void_p, c_size_t, c_size_t, c_size_t, c_double)

    @staticmethod
    def update_cond(seepage, network=None, fa_id=None, fw_max=None, layer_dh=None,
                    ca_g=None, ca_l=None, ca_h=None):
        """
        更新Seepage系统中各个Face的Cond属性(根据裂缝单元的长度、缝宽、高度来计算).
            或者更新各个Cell的Cond属性(暂存到ca_g中)
        """
        assert isinstance(seepage, Seepage)
        if fw_max is None:
            fw_max = 0.005
        if ca_g is not None and ca_l is not None and ca_h is not None:
            core.hf2_alg_update_cond1(seepage.handle, ca_g, ca_l, ca_h, fw_max)
        else:
            assert isinstance(network, FractureNetwork2)
            if layer_dh is None:
                layer_dh = -1  # 此时，将采用fracture的高度属性
            core.hf2_alg_update_cond0(seepage.handle, network.handle, fw_max, fa_id, layer_dh)

    core.use(None, 'hf2_alg_update_pore0', c_void_p, c_void_p, c_size_t)
    core.use(None, 'hf2_alg_update_pore1', c_void_p, c_size_t, c_size_t, c_double)
    core.use(None, 'hf2_alg_update_pore2', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t)
    core.use(None, 'hf2_alg_update_pore3', c_void_p, c_size_t, c_size_t, c_double, c_double)

    @staticmethod
    def update_pore(seepage, manager=None, fa_id=None, ca_s=None, ca_ny=None, dw=None, ca_l=None,
                    ca_h=None, ca_g=None, ca_mu=None, k1=None, k2=None):
        """
        更新渗流系统的pore.
        其中：
            manager: 二维裂缝管理 InfManager2
            fa_id: 裂缝中存储对应Cell的ID的属性
            ca_s：定义Cell对应的裂缝的面积
            ca_ny: 定义垂直于裂缝面的应力（以拉张为正）
            dw: 定义压力变化1Pa，裂缝的宽度改变的幅度(单位: m)
            ca_l: 定义Cell对应裂缝的长度
            ca_h：定义Cell对应裂缝的高度
            ca_g: 定义Cell位置的剪切模量
            ca_mu: 定义Cell位置的泊松比
        注意：
            当指定manager的时候，则使用manager来更新，否则，则使用seepage中定义的ca_s，ca_ny以及
            给定的dw来更新.
        """
        assert isinstance(seepage, Seepage)
        if ca_ny is not None and ca_s is not None and k1 is not None and k2 is not None:
            # 此时建议的取值: k1=1.0e-10, k2=1.0e-8
            core.hf2_alg_update_pore3(seepage.handle, ca_ny, ca_s, k1, k2)
            return

        if isinstance(manager, InfManager2):
            assert fa_id is not None
            core.hf2_alg_update_pore0(seepage.handle, manager.handle, fa_id)
            return

        if ca_s is not None and ca_ny is not None and dw is not None:
            # will be removed in the future.
            core.hf2_alg_update_pore1(seepage.handle, ca_s, ca_ny, dw)
            return

        if ca_l is not None and ca_h is not None and ca_ny is not None and ca_g is not None and ca_mu is not None:
            core.hf2_alg_update_pore2(seepage.handle, ca_l, ca_h, ca_ny, ca_g, ca_mu)
            return

        assert False

    core.use(None, 'hf2_alg_update_area', c_void_p, c_size_t, c_void_p, c_size_t, c_double)

    @staticmethod
    def update_area(seepage, ca_s, network, fa_id, fh=None):
        """
        更新存储在Seepage的各个Cell中的对应的裂缝的面积属性.
        其中：
            ca_s：   为需要更新的面积属性的ID
            network：为裂缝网络
            fa_id：  为存储在各个裂缝单元中的对应的Cell的ID
            fh:     为裂缝的高度，当这个值为负值的时候，则使用定义在裂缝单元内的高度
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork2)
        if fh is None:
            fh = -1.0  # Now, using the fracture height
        core.hf2_alg_update_area(seepage.handle, ca_s, network.handle, fa_id, fh)

    core.use(None, 'hf2_alg_update_length', c_void_p, c_size_t, c_void_p, c_size_t)

    @staticmethod
    def update_length(seepage, ca_l, network, fa_id):
        """
        更新各个Cell的裂缝长度属性
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(network, FractureNetwork2)
        core.hf2_alg_update_length(seepage.handle, ca_l, network.handle, fa_id)

    core.use(None, 'hf2_alg_update_normal_stress', c_void_p, c_size_t, c_void_p, c_size_t, c_bool, c_double)

    @staticmethod
    def update_normal_stress(seepage, ca_ny, manager, fa_id, except_self=True, relax_factor=1.0):
        """
        更新裂缝的法向应力(以拉应力为正)，并存储在裂缝对应Cell的ca_ny属性上.
        注意:
            这个函数会首先删除掉seepage中所有的Cell的ca_ny属性，然后在遍历所有的裂缝，计算应力，然后给定裂缝的fa_id属性
            找到对应的Cell，然后在Cell上添加ca_ny属性. 因此，这个函数运行之后，只要某个Cell定义了ca_ny属性，那么ca_ny
            对应的数值就一定是最新的.
        注意：
            当except_self为True的时候，则去除了当前单元的影响，即假设当前单元的开度为0.
        """
        assert isinstance(seepage, Seepage)
        assert isinstance(manager, InfManager2)
        core.hf2_alg_update_normal_stress(seepage.handle, ca_ny, manager.handle, fa_id, except_self, relax_factor)

    core.use(None, 'hf2_alg_exchange_fluids', c_void_p, c_void_p, c_double, c_size_t, c_size_t)

    @staticmethod
    def exchange_fluids(layers, pipe, dt, ca_g, ca_fp=None):
        """
        在不同的层之间交换流体
        """
        if not isinstance(layers, PtrVector):
            layers = PtrVector.from_objects(layers)
        assert isinstance(pipe, Seepage)
        if ca_fp is None:
            ca_fp = 99999999  # Now, will not update fluid pressure
        core.hf2_alg_exchange_fluids(layers.handle, pipe.handle, dt, ca_g, ca_fp)

    core.use(c_bool, 'hf2_alg_rect_v3_intersected', c_double, c_double, c_double, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double, c_double, c_double)

    @staticmethod
    def rect_v3_intersected(a, b):
        """
        返回两个给定的竖直裂缝a和b是否相交
        """
        assert len(a) == 6 and len(b) == 6
        return core.hf2_alg_rect_v3_intersected(*a, *b)

    core.use(None, 'hf2_alg_create_links', c_void_p, c_void_p, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t,
             c_double, c_double, c_double, c_double, c_double, c_double)

    @staticmethod
    def create_links(seepage, cell_n, keys, v3, buf=None):
        """
        对于seepage模型，读取cell中定义的竖直的矩形的信息，返回和给定的矩形相交的所有的Cell的ID
        """
        if buf is None:
            buf = UintVector()
        assert isinstance(seepage, Seepage)
        assert len(v3) == 6
        core.hf2_alg_create_links(buf.handle, seepage.handle, cell_n,
                                  keys.x1, keys.y1, keys.z1,
                                  keys.x2, keys.y2, keys.z2, *v3)
        return buf.to_list()


class FracScatter3(HasHandle):
    """
    将裂缝离散成为散点，从而判断裂缝之间的位置关系
    """
    core.use(c_void_p, 'new_fsc3')
    core.use(None, 'del_fsc3', c_void_p)

    def __init__(self, path=None, handle=None):
        super(FracScatter3, self).__init__(handle, core.new_fsc3, core.del_fsc3)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'fsc3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.fsc3_save(self.handle, make_c_char_p(path))

    core.use(None, 'fsc3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.fsc3_load(self.handle, make_c_char_p(path))

    core.use(None, 'fsc3_write_fmap', c_void_p, c_void_p, c_char_p)
    core.use(None, 'fsc3_read_fmap', c_void_p, c_void_p, c_char_p)

    def to_fmap(self, fmt='binary'):
        """
        将数据序列化到一个Filemap中. 其中fmt的取值可以为: text, xml和binary
        """
        fmap = FileMap()
        core.fsc3_write_fmap(self.handle, fmap.handle, make_c_char_p(fmt))
        return fmap

    def from_fmap(self, fmap, fmt='binary'):
        """
        从Filemap中读取序列化的数据. 其中fmt的取值可以为: text, xml和binary
        """
        assert isinstance(fmap, FileMap)
        core.fsc3_read_fmap(self.handle, fmap.handle, make_c_char_p(fmt))

    @property
    def fmap(self):
        return self.to_fmap(fmt='binary')

    @fmap.setter
    def fmap(self, value):
        self.from_fmap(value, fmt='binary')

    core.use(None, 'fsc3_set_gr', c_void_p, c_double, c_double, c_double, c_double, c_double, c_double)

    def set_gr(self, center, offset):
        """
        设置格子
        """
        assert len(center) == 3
        assert len(offset) == 3
        core.fsc3_set_gr(self.handle, *center, *offset)

    core.use(None, 'fsc3_set', c_void_p, c_size_t,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double)

    def set(self, idx, center, p0, p1):
        """
        设置一个裂缝，并且自动生成它的散点. 其中center为三维矩形的中心点坐标, p0和p1分别为两个相邻的边的中心点的坐标.
        """
        assert len(center) == 3
        assert len(p0) == 3
        assert len(p1) == 3
        core.fsc3_set(self.handle, idx, *center, *p0, *p1)

    core.use(c_size_t, 'fsc3_size', c_void_p)
    core.use(None, 'fsc3_resize', c_void_p, c_size_t)

    @property
    def size(self):
        return core.fsc3_size(self.handle)

    @size.setter
    def size(self, value):
        core.fsc3_resize(self.handle, value)

    core.use(c_size_t, 'fsc3_get_intersection', c_void_p, c_size_t, c_size_t)

    def get_intersection(self, i0, i1):
        return core.fsc3_get_intersection(self.handle, i0, i1)


class Hf3Alg:
    """
    用于辅助实现三维压裂计算（Debugging）
    """
    core.use(None, 'hf3_alg_set_nf_zero_ikr', c_void_p, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def set_nf_zero_ikr(model, nf_n, fid, ikr):
        """
        在和天然裂缝相关的那些face中，将fid的相渗设置为ikr
        """
        assert isinstance(model, Seepage)
        core.hf3_alg_set_nf_zero_ikr(model.handle, nf_n, fid, ikr)

    core.use(None, 'hf3_alg_find_intersected_nfs', c_void_p, c_void_p, c_size_t, c_size_t,
             c_double, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def find_intersected_nfs(model, nf_n, hf_id, ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2, leps=None, buffer=None):
        """
        查找与给定的hf相交的nf的id，并且存储到buffer. 返回一个UintVector.
        """
        assert isinstance(model, Seepage)
        assert 0 <= nf_n <= hf_id < model.cell_number
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        if leps is None:
            leps = -1
        else:
            assert 0 < leps < 1.0e3
        core.hf3_alg_find_intersected_nfs(buffer.handle, model.handle, nf_n, hf_id, leps,
                                          ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2)
        return buffer

    core.use(None, 'hf3_alg_get_new_cells', c_void_p, c_void_p, c_size_t)

    @staticmethod
    def get_new_cells(model, ca_is_new, buffer=None):
        """
        返回ca_is_new属性等于1的所有Cell的ID
        """
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        assert isinstance(model, Seepage)
        core.hf3_alg_get_new_cells(buffer.handle, model.handle, ca_is_new)
        return buffer

    core.use(None, 'hf3_alg_update_pore', c_void_p, c_double, c_double, c_void_p,
             c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def update_pore(model, thick, pore_modulus, cell_ids, ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2):
        """
        更新孔隙空间
        """
        assert isinstance(model, Seepage)
        assert isinstance(cell_ids, UintVector)
        core.hf3_alg_update_pore(model.handle, thick, pore_modulus, cell_ids.handle,
                                 ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2)

    core.use(None, 'hf3_alg_set_attr', c_void_p, c_size_t, c_double, c_void_p)

    @staticmethod
    def set_attr(model, index, value, cell_ids):
        """
        对于给定的Cell，设置属性到给定的数值
        """
        assert isinstance(model, Seepage)
        assert isinstance(cell_ids, UintVector)
        core.hf3_alg_set_attr(model.handle, index, value, cell_ids.handle)

    core.use(None, 'hf3_alg_update_rc3', c_void_p,
             c_void_p, c_size_t, c_size_t, c_double,
             c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def update_rc3(flow, network, fixed_n, layer_n, thick,
                   ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2):
        """
        根据network来更新model的rc3属性; 会修改node的x和y坐标为裂缝的中心点（z不变）；
        之后，再在这个位置的基础上，修改x1、y1、z1和x2、y2、z2属性.
        """
        assert isinstance(flow, Seepage)
        assert isinstance(network, FractureNetwork2)
        core.hf3_alg_update_rc3(flow.handle, network.handle, fixed_n, layer_n, thick,
                                ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2)

    core.use(None, 'hf3_alg_update_pc', c_void_p, c_void_p,
             c_void_p, c_void_p,
             c_double, c_double, c_double, c_double, c_double, c_double,
             c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def update_pc(model, cell_ids, insitu_stress, strength, left, right,
                  ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2, ca_pc):
        """
        计算临界的压力，当实际压力超过这个压力的时候，裂缝可以扩展
        """
        assert isinstance(model, Seepage)
        assert isinstance(cell_ids, UintVector)
        assert isinstance(insitu_stress, Tensor3Matrix3)
        assert isinstance(strength, Tensor3Matrix3)
        assert len(left) == 3
        assert len(right) == 3
        core.hf3_alg_update_pc(model.handle, cell_ids.handle, insitu_stress.handle, strength.handle,
                               left[0], left[1], left[2], right[0], right[1], right[2],
                               ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2, ca_pc)

    core.use(None, 'hf3_alg_classify_cells', c_void_p, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def classify_cells(model, fixed_n, ca_tag=None, ca_pc=None):
        """
        将Cell分成4类(写入cell的tag属性)：
            1、天然裂缝(未打开的裂缝)
            2、天然裂缝(打开)
            3、水力裂缝(未打开的裂缝)
            4、水力裂缝(打开)
        """
        assert isinstance(model, Seepage)
        if ca_tag is None:
            ca_tag = model.reg_cell_key('tag')
        if ca_pc is None:
            ca_pc = model.get_cell_key('pc')
        core.hf3_alg_classify_cells(model.handle, fixed_n, ca_tag, ca_pc)

    core.use(None, 'hf3_alg_classify_faces', c_void_p, c_size_t, c_size_t)

    @staticmethod
    def classify_faces(model, fa_tag=None, ca_tag=None):
        """
        这样，将Face分为
            1、打开的水力裂缝内部以及周边的Face
            2、打开的天然裂缝内部以及周边的Face
            3、其它尚未被打开的裂缝内部的Face
        """
        assert isinstance(model, Seepage)
        if fa_tag is None:
            fa_tag = model.reg_face_key('tag')
        if ca_tag is None:
            ca_tag = model.get_cell_key('tag')
        core.hf3_alg_classify_faces(model.handle, fa_tag, ca_tag)

    core.use(None, "hf3_alg_update_cell_len", c_void_p, c_void_p,
             c_size_t, c_size_t, c_size_t, c_size_t)

    @staticmethod
    def update_cell_len(model, network, ca_len=None, fa_id=None, ma_layer_n=None, ma_fixed_n=None):
        assert isinstance(model, Seepage)
        assert isinstance(network, FractureNetwork2)
        if ca_len is None:
            ca_len = model.reg_cell_key('len')
        if fa_id is None:
            fa_id = model.get_key('fr_id')
        if ma_layer_n is None:
            ma_layer_n = model.get_model_key('layer_n')
        if ma_fixed_n is None:
            ma_fixed_n = model.get_model_key('fixed_n')

        core.hf3_alg_update_cell_len(model.handle, network.handle, ca_len, fa_id, ma_layer_n, ma_fixed_n)

    core.use(None, 'hf3_alg_update_face_geometry', c_void_p,
             c_size_t, c_size_t, c_size_t,
             c_double,
             c_size_t, c_size_t,
             c_size_t,
             c_double, c_double)

    @staticmethod
    def update_face_geometry(model, fa_s=None, fa_l=None, ca_len=None,
                             pore_thick=None, fixed_n=None, fixed_face_n=None, layer_n=None, z0=None, z1=None):
        """
        更新bond的几何（仅仅更新水力裂缝内部的已经连接水力裂缝和天然裂缝的）
        """
        assert isinstance(model, Seepage)
        if fa_s is None:
            fa_s = model.reg_face_key('area')
        if fa_l is None:
            fa_l = model.reg_face_key('length')
        if ca_len is None:
            ca_len = model.get_cell_key('len')
        if pore_thick is None:
            pore_thick = model.get_attr(model.get_model_key('pore_thick'))
        if fixed_n is None:
            fixed_n = round(model.get_attr(model.get_model_key('fixed_n')))
        if fixed_face_n is None:
            fixed_face_n = round(model.get_attr(model.get_model_key('fixed_face_n')))
        if layer_n is None:
            layer_n = round(model.get_attr(model.get_model_key('layer_n')))
        if z0 is None:
            z0 = model.get_attr(model.get_model_key('z0'))
        if z1 is None:
            z1 = model.get_attr(model.get_model_key('z1'))
        core.hf3_alg_update_face_geometry(model.handle, fa_s, fa_l, ca_len, pore_thick,
                                          fixed_n, fixed_face_n, layer_n, z0, z1)

    @staticmethod
    def update_seepage_topology(seepage, fixed_n, layer_n, network, fa_id, fa_new, z_range,
                                cell_new=None, face_new=None, fixed_face_n=None,
                                pre_task=None):
        """
        根据二维裂缝网络的结构，来更新seepage的结构。

        假设seepage中的单元分为两类，分别为固定单元（代表天然裂缝）和活动单元（主裂缝）。
        在seepage中，共有fixed_n个固定单元。这些固定单元在前面，活动单元在后面.

        活动的单元又分为layer_n层，且每层的单元的数量和网络的结构是完全相同的.

        在network的每一个裂缝中，都存储一个属性fa_id，表示这个单元对应的seepage每一层的
        cell的id.

        计算主要分为3步：
            1、将最后的layer_n层Cell弹出来;
            2、利用network的结构来更新这些层；
            3、将更新了结构的Cell和Face再重新压入到seepage中，并且建立这些层之间的连接(Face)

        返回：
            新的裂缝单元的数量.

        参数：
            cell_new: cell的属性ID，表示cell是否是新的；
            face_new: face的属性ID，表示face是否是新的；
            pre_task: 如果结构过期需要更新，则首先执行这个任务，否则，则不要执行

        注意：
            如果调整了结构(会首先判断结构是否过期)，那么对于活动的cell，其额外添加的那些face将会被删除掉.
        """
        assert isinstance(network, FractureNetwork2)
        assert isinstance(seepage, Seepage)
        if not Hf2Alg.seepage_topology_expired(network, fa_id):
            if cell_new is not None:
                seepage.cells_read(index=cell_new, value=0)
            if face_new is not None:
                seepage.faces_read(index=face_new, value=0)
            for frac in network.get_fractures():
                frac.set_attr(fa_new, value=0)
            return 0

        if pre_task is not None:
            pre_task()

        assert fixed_n <= seepage.cell_number
        assert layer_n >= 1
        assert fa_id is not None
        assert fa_new is not None

        active_n = seepage.cell_number - fixed_n
        assert active_n % layer_n == 0
        layer_cell_n = active_n // layer_n
        assert isinstance(layer_cell_n, int)  # 必须确保是int，否则后面传入dll的时候会出错
        assert layer_cell_n * layer_n + fixed_n == seepage.cell_number

        # 将最后的layer_n层Cell弹出来
        layers = []
        ibeg = fixed_n
        for layer_i in range(layer_n):
            lay = Seepage()
            while lay.cell_number < layer_cell_n:
                lay.add_cell()
            assert lay.cell_number == layer_cell_n
            kwargs = create_dict(ibeg0=0, other=seepage, ibeg1=ibeg, count=layer_cell_n)
            lay.clone_cells(**kwargs)
            lay.clone_inner_faces(**kwargs)
            layers.append(lay)
            ibeg += layer_cell_n
        # 将所有活动的cell抛出（这会带来一个副作用，就是所有这些cell相关的face，也会被删除）;
        seepage.pop_cells(active_n)
        assert seepage.cell_number == fixed_n
        if fixed_face_n is not None:
            assert seepage.face_number == fixed_face_n

        # 利用network的结构来更新这些层
        fractures = network.get_fractures()
        cell_ids = []  # 备份fa_id
        for frac in fractures:
            cell_ids.append(frac.get_attr(fa_id))
        for layer_i in range(layer_n):
            if layer_i > 0:  # 恢复备份的fa_id (第一层不需要)
                for i in range(len(fractures)):
                    frac = fractures[i]
                    frac.set_attr(fa_id, cell_ids[i])
            lay = layers[layer_i]
            Hf2Alg.update_seepage_topology(seepage=lay, network=network, fa_id=fa_id,
                                           fa_new=fa_new, cell_new=cell_new, face_new=face_new
                                           )

        # 更新各个Cell的位置
        z_min, z_max = (-1, 1) if z_range is None else z_range
        layer_h = (z_max - z_min) / layer_n
        layer_z = [z_min + layer_h * (layer_i + 0.5) for layer_i in range(layer_n)]
        new_n = 0  # 新的裂缝单元的数量
        for frac in network.get_fractures():
            is_new = frac.get_attr(fa_new)
            if abs(is_new - 1) > 0.1:  # 对于新的裂缝，is_new的数值等于1
                continue
            new_n += 1
            x0, y0, x1, y1 = frac.pos
            x = (x0 + x1) / 2
            y = (y0 + y1) / 2
            cell_id = round(frac.get_attr(fa_id))
            for layer_i in range(layer_n):
                lay = layers[layer_i]
                assert 0 <= cell_id < lay.cell_number
                cell = lay.get_cell(cell_id)
                cell.pos = (x, y, layer_z[layer_i])

        # 将更新了结构的Cell和Face再重新压入到seepage中，并且建立这些层之间的连接(Face)
        for layer_i in range(layer_n):
            lay = layers[layer_i]
            if layer_i == 0:  # 仅仅追加，不创建Face
                seepage.append(lay, cell_i0=None)
            else:  # 追加，并且添加和前面一层的Face
                cell_i0 = seepage.cell_number - lay.cell_number
                assert cell_i0 >= 0
                seepage.append(lay, cell_i0=cell_i0)

        assert new_n > 0, f'new_n = {new_n} since the seepage topology is expired'
        return new_n

    core.use(None, 'hf3_alg_cell_ini', c_void_p, c_void_p,
             c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_double)

    @staticmethod
    def cell_ini(seepage, cell_ids, ca_vol, ca_t, ca_mc, fa_t, fa_c,
                 temperature=280.0):
        """
        对给定序号的Cell进行初始化
        """
        core.hf3_alg_cell_ini(seepage.handle, cell_ids.handle, ca_vol,
                              ca_t, ca_mc, fa_t, fa_c, temperature)

    core.use(None, 'hf3_alg_face_ini', c_void_p, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t, c_double, c_double)

    @staticmethod
    def face_ini(seepage, i_beg, i_end, fa_s, fa_l, fa_tag, hf_perm, ratio=10.0):
        core.hf3_alg_face_ini(seepage.handle, i_beg, i_end, fa_s, fa_l, fa_tag, hf_perm, ratio)

    core.use(c_size_t, 'hf3_alg_count_cells', c_void_p, c_size_t, c_double, c_double)

    @staticmethod
    def count_cells(seepage, ca_tag, tag, eps=0.1):
        """
        返回tag等于给定值的Cell的数量
        """
        return core.hf3_alg_count_cells(seepage.handle, ca_tag, tag, eps)

    core.use(None, 'hf3_alg_update_area_by_rc3', c_void_p, c_size_t,
             c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_void_p)

    @staticmethod
    def update_area_by_rc3(seepage, ca_s, ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2, cell_ids=None):
        """
        根据rc3属性来计算面积
        """
        assert isinstance(seepage, Seepage)
        if cell_ids is None:
            core.hf3_alg_update_area_by_rc3(seepage.handle,
                                            ca_s, ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2, 0)
        else:
            assert isinstance(cell_ids, UintVector)
            core.hf3_alg_update_area_by_rc3(seepage.handle,
                                            ca_s, ca_x1, ca_y1, ca_z1, ca_x2, ca_y2, ca_z2, cell_ids.handle)


class Sigma3:
    core.use(None, 'sigma3_get1', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double)

    core.use(None, 'sigma3_get2', c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double)

    @staticmethod
    def get(pos, disp, G, mu, area=None, triangle=None, buffer=None):
        """
        返回诱导应力.
        """
        if not isinstance(buffer, Tensor3):
            buffer = Tensor3()
        if area is not None:
            core.sigma3_get1(buffer.handle, pos[0], pos[1], pos[2], disp[0], disp[1], disp[2], area, G, mu)
            return buffer
        else:
            assert triangle is not None
            p0, p1, p2 = triangle
            x0, y0, z0 = p0
            x1, y1, z1 = p1
            x2, y2, z2 = p2
            core.sigma3_get2(buffer.handle, pos[0], pos[1], pos[2],
                             x0, y0, z0,
                             x1, y1, z1,
                             x2, y2, z2,
                             disp[0], disp[1], disp[2],
                             G, mu)
            return buffer


if __name__ == '__main__':
    print(core.time_compile)
