import os
from ctypes import c_void_p, c_char_p, c_int, c_bool, c_double, c_size_t

from zml import (DllCore, HasHandle, load_cdll, make_c_char_p, Vector, Lattice3,
                 UintVector, Interp1, is_array,
                 Interp3, clock, Matrix3)

core = DllCore(dll_obj=load_cdll(name='dsmc.dll',
                                 first=os.path.dirname(__file__)))


class Molecule(HasHandle):
    """
    模拟分子。模拟分子和真实的分子有很大的区别。为了降低计算规模，在DSMC计算时，一个模拟分子
    会代表大量的真实分子，从而大大降低计算量，使得DSMC方法可以计算较大的计算区域。
    """
    core.use(c_void_p, 'new_molecule')
    core.use(None, 'del_molecule', c_void_p)

    def __init__(self, handle=None, **kwargs):
        """
        分子的初始化
        """
        super(Molecule, self).__init__(handle, core.new_molecule,
                                       core.del_molecule)
        if handle is None:
            self.set(**kwargs)

    def __str__(self):
        return f'Molecule(mass={self.mass}, radi={self.radi}, pos={self.pos}, vel={self.vel})'

    core.use(None, 'molecule_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.molecule_save(self.handle, make_c_char_p(path))

    core.use(None, 'molecule_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.molecule_load(self.handle, make_c_char_p(path))

    core.use(c_double, 'molecule_get_pos', c_void_p, c_size_t)
    core.use(None, 'molecule_set_pos', c_void_p, c_size_t, c_double)

    @property
    def pos(self):
        """
        模拟分子的中心点在三维空间的位置
        """
        return [core.molecule_get_pos(self.handle, i) for i in range(3)]

    @pos.setter
    def pos(self, val):
        """
        模拟分子的中心点在三维空间的位置
        """
        assert len(val) == 3
        for i in range(3):
            core.molecule_set_pos(self.handle, i, val[i])

    core.use(c_double, 'molecule_get_vel', c_void_p, c_size_t)
    core.use(None, 'molecule_set_vel', c_void_p, c_size_t, c_double)

    @property
    def vel(self):
        """
        模拟分子在三维空间的速度
        """
        return [core.molecule_get_vel(self.handle, i) for i in range(3)]

    @vel.setter
    def vel(self, val):
        """
        模拟分子在三维空间的速度
        """
        assert len(val) == 3
        for i in range(3):
            core.molecule_set_vel(self.handle, i, val[i])

    core.use(c_double, 'molecule_get_mass', c_void_p)
    core.use(None, 'molecule_set_mass', c_void_p, c_double)

    @property
    def mass(self):
        """
        模拟分子的质量 [kg]
        """
        return core.molecule_get_mass(self.handle)

    @mass.setter
    def mass(self, val):
        """
        模拟分子的质量 [kg]
        """
        core.molecule_set_mass(self.handle, val)

    core.use(c_double, 'molecule_get_radi', c_void_p)
    core.use(None, 'molecule_set_radi', c_void_p, c_double)

    @property
    def radi(self):
        """
        模拟分子的半径。用以定义模拟分子的碰撞。只有当两个模拟分子之间的距离小于二者的半径之和的时候，
        它们才会碰撞。因此，可以通过修改分子的半径来修改它与其它分子发生碰撞的可能。
        """
        return core.molecule_get_radi(self.handle)

    @radi.setter
    def radi(self, val):
        core.molecule_set_radi(self.handle, val)

    core.use(c_double, 'molecule_get_imass', c_void_p)
    core.use(None, 'molecule_set_imass', c_void_p, c_double)

    @property
    def imass(self):
        """
        模拟分子的内部质量。除了定义的外在质量之外，假设模拟分子内部的分子还在做不规则的
        热运动，这部分运动会存储一部分能量。这部分振动的动能会在模拟分子相互碰撞的过程中
        积聚或者释放出来。内部质量越大，则储存能量的能力就越强。
        """
        return core.molecule_get_imass(self.handle)

    @imass.setter
    def imass(self, val):
        core.molecule_set_imass(self.handle, val)

    core.use(c_double, 'molecule_get_ivel', c_void_p)
    core.use(None, 'molecule_set_ivel', c_void_p, c_double)

    @property
    def ivel(self):
        """
        模拟分子内部分子团做无规则运动的速度
        """
        return core.molecule_get_ivel(self.handle)

    @ivel.setter
    def ivel(self, val):
        core.molecule_set_ivel(self.handle, val)

    core.use(c_double, 'molecule_get_relax_dt', c_void_p)
    core.use(None, 'molecule_set_relax_dt', c_void_p, c_double)

    @property
    def relax_dt(self):
        """
        模拟分子的内部能量和模拟分子动能相互转化的松弛时间
        """
        return core.molecule_get_relax_dt(self.handle)

    @relax_dt.setter
    def relax_dt(self, val):
        core.molecule_set_relax_dt(self.handle, val)

    core.use(c_int, 'molecule_get_tag', c_void_p)
    core.use(None, 'molecule_set_tag', c_void_p, c_int)

    @property
    def tag(self):
        """
        分子的标签<大于等于0为正常的分子，小于0为沙子>
        """
        return core.molecule_get_tag(self.handle)

    @tag.setter
    def tag(self, value):
        """
        分子的标签<大于等于0为正常的分子，小于0为沙子>
        """
        core.molecule_set_tag(self.handle, value)

    core.use(None, 'molecule_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        从另外一个分子复制所有的数据
        """
        assert isinstance(other, Molecule)
        core.molecule_clone(self.handle, other.handle)


class MoleVec(HasHandle):
    """
    一个由模拟分子组成的数组
    """
    core.use(c_void_p, 'new_vmole')
    core.use(None, 'del_vmole', c_void_p)

    def __init__(self, handle=None):
        super(MoleVec, self).__init__(handle, core.new_vmole, core.del_vmole)

    def __str__(self):
        return f'Moles(size={len(self)})'

    core.use(None, 'vmole_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.vmole_save(self.handle, make_c_char_p(path))

    core.use(None, 'vmole_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.vmole_load(self.handle, make_c_char_p(path))

    core.use(None, 'vmole_clear', c_void_p)

    def clear(self):
        """
        清除所有的分子
        """
        core.vmole_clear(self.handle)

    core.use(None, 'vmole_push_back', c_void_p, c_void_p)
    core.use(None, 'vmole_push_back_multi', c_void_p, c_void_p, c_void_p,
             c_void_p, c_void_p)
    core.use(None, 'vmole_push_back_other', c_void_p, c_void_p)
    core.use(None, 'vmole_push_back_other_with_tag', c_void_p, c_void_p, c_int)

    def append(self, mole=None, vx=None, vy=None, vz=None, moles=None,
               tag=None):
        """
        添加一个分子<或者多个分子>；当给定的一系列坐标值给定的时候，则利用mole定义的数据，以及vx,vy,vz定义的位置来添加多个分析
        """
        if mole is not None:
            assert isinstance(mole, Molecule)
            if isinstance(vx, Vector) and isinstance(vy, Vector) and isinstance(
                    vz, Vector):
                core.vmole_push_back_multi(self.handle, mole.handle, vx.handle,
                                           vy.handle, vz.handle)
            else:
                core.vmole_push_back(self.handle, mole.handle)
        if moles is not None:
            if tag is not None:
                core.vmole_push_back_other_with_tag(self.handle, moles.handle,
                                                    tag)
            else:
                core.vmole_push_back_other(self.handle, moles.handle)

    core.use(c_size_t, 'vmole_size', c_void_p)

    def __len__(self):
        """
        返回分子的数量
        """
        return core.vmole_size(self.handle)

    core.use(c_void_p, 'vmole_get', c_void_p, c_size_t)

    def __getitem__(self, index):
        """
        返回index位置的分子数据
        """
        if index < len(self):
            return Molecule(handle=core.vmole_get(self.handle, index))

    core.use(None, 'vmole_update_pos', c_void_p,
             c_double, c_double, c_double,
             c_double)

    def update_pos(self, gravity, dt):
        """
        更新各个粒子的位置(当重力不等于0的时候，将同时会修改粒子的速度)
        """
        assert len(gravity) == 3
        core.vmole_update_pos(self.handle, *gravity, dt)

    core.use(None, 'vmole_get_pos', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_pos(self, x=None, y=None, z=None):
        """
        获得所有粒子的x,y,z坐标
        """
        if x is None:
            x = Vector()
        if y is None:
            y = Vector()
        if z is None:
            z = Vector()
        core.vmole_get_pos(self.handle, x.handle, y.handle, z.handle)
        return x, y, z

    core.use(None, 'vmole_get_vel', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_vel(self, x=None, y=None, z=None):
        """
        获得所有粒子的x,y,z坐标
        """
        if x is None:
            x = Vector()
        if y is None:
            y = Vector()
        if z is None:
            z = Vector()
        core.vmole_get_vel(self.handle, x.handle, y.handle, z.handle)
        return x, y, z

    core.use(None, 'vmole_collision', c_void_p, c_void_p, c_void_p, c_void_p)

    def collision(self, lat, vi0=None, vi1=None):
        """
        施加碰撞操作<需要提前将粒子放入到格子里，只有在格子里面的模拟分子才会参与碰撞>；
        当给定vi0和vi1的时候，则记录碰撞对
        """
        assert isinstance(lat, Lattice3)
        if isinstance(vi0, UintVector) and isinstance(vi1, UintVector):
            core.vmole_collision(self.handle, lat.handle, vi0.handle,
                                 vi1.handle)
            return vi0, vi1
        else:
            core.vmole_collision(self.handle, lat.handle, 0, 0)

    core.use(None, 'vmole_update_internal_energy', c_void_p, c_void_p, c_void_p,
             c_double)

    def update_internal_energy(self, vi0, vi1, dt):
        """
        利用给定的碰撞对，在碰撞对之间，施加内能和动能之间的相互转化
        """
        core.vmole_update_internal_energy(self.handle, vi0.handle, vi1.handle,
                                          dt)

    core.use(None, 'vmole_rand_add', c_void_p, c_void_p, c_size_t)

    def rand_add(self, other, count):
        """
        从给定的分子源随机拷贝过来count数量的分子，用于分子的生成
        """
        assert isinstance(other, MoleVec)
        core.vmole_rand_add(self.handle, other.handle, count)

    core.use(c_double, 'vmole_get_vel_max', c_void_p)

    def get_vmax(self):
        """
        返回所有分子速度的最大值，主要用于确定时间步长
        """
        return core.vmole_get_vel_max(self.handle)

    core.use(None, 'vmole_add_offset', c_void_p, c_double, c_double, c_double)

    def add_offset(self, dx, dy, dz):
        """
        所有分子的位置施加一个整体的移动
        """
        core.vmole_add_offset(self.handle, dx, dy, dz)

    core.use(None, 'vmole_get_range', c_void_p, c_void_p)

    def get_range(self):
        """
        获得所有分子位置的范围
        """
        if len(self) > 0:
            v = Vector()
            core.vmole_get_range(self.handle, v.handle)
            assert len(v) == 6
            return (v[0], v[1], v[2]), (v[3], v[4], v[5])

    core.use(c_size_t, 'vmole_erase', c_void_p, c_void_p)

    def erase(self, reg3):
        """
        删除指定区域内的分子
        """
        assert isinstance(reg3, Region3)
        return core.vmole_erase(self.handle, reg3.handle)

    core.use(c_size_t, 'vmole_roll_back', c_void_p, c_void_p, c_double, c_bool)
    core.use(c_size_t, 'vmole_roll_back_record', c_void_p, c_void_p, c_double,
             c_bool, c_void_p, c_double, c_double)

    def roll_back(self, reg3, fmap=None, dt=None, time_span=None, parallel=True,
                  diffuse_ratio=1.0):
        """
        从给定的区域内退出. 当给定fmap的时候，将记录冲击固体的力.
        其中：
            parallel: 内核是否调用并行
            diffuse_ratio: 为(tag>=的普通分子)漫反射发生的比例(注意tag<0的分子必然发生镜面反射，不受此参数影响).
        """
        assert isinstance(reg3, Region3)
        if fmap is None:
            return core.vmole_roll_back(self.handle, reg3.handle, diffuse_ratio,
                                        parallel)
        else:
            assert isinstance(fmap, ForceMap)
            assert dt is not None and time_span is not None
            return core.vmole_roll_back_record(self.handle, reg3.handle,
                                               diffuse_ratio, parallel,
                                               fmap.handle, dt, time_span)

    core.use(None, 'vmole_get_mass', c_void_p, c_void_p)

    def get_mass(self, vm=None):
        """
        获得所有模拟分子的质量(作为一个Vector返回)
        """
        if vm is None:
            vm = Vector()
        core.vmole_get_mass(self.handle, vm.handle)
        return vm

    core.use(None, 'vmole_update_radi', c_void_p, c_void_p)

    def update_radi(self, v2r):
        """
        根据各个模拟分子的速度来更新它的碰撞半径
        """
        assert isinstance(v2r, Interp1)
        core.vmole_update_radi(self.handle, v2r.handle)

    core.use(None, 'vmole_get_radi', c_void_p, c_void_p)

    def get_radi(self, vr=None):
        """
        备份分子的半径
        """
        if not isinstance(vr, Vector):
            vr = Vector()
        core.vmole_backup_radi(self.handle, vr.handle)
        return vr

    core.use(None, 'vmole_set_radi', c_void_p, c_void_p)

    def set_radi(self, vr):
        """
        设置分子的半径
        """
        assert isinstance(vr, Vector)
        core.vmole_set_radi(self.handle, vr.handle)

    core.use(c_size_t, 'vmole_count_tag', c_void_p, c_int)

    def count_tag(self, tag):
        """
        返回具有给定tag的分子的数量
        """
        return core.vmole_count_tag(self.handle, tag)

    core.use(None, 'vmole_clamp_pos', c_void_p, c_size_t, c_double, c_double)

    def clamp_pos(self, idim, left, right):
        """
        对分子在idim维度上的位置进行约束
        """
        core.vmole_clamp_pos(self.handle, idim, left, right)


class Region3(HasHandle):
    """
    定义一个三维的区域。数据被放在格子里面，便于高效率地访问 （用于dsmc）
    """
    core.use(c_void_p, 'new_region3')
    core.use(None, 'del_region3', c_void_p)

    def __init__(self, box=None, shape=None, value=None, handle=None):
        super(Region3, self).__init__(handle, core.new_region3,
                                      core.del_region3)
        if handle is None:
            if box is not None and shape is not None:
                self.create(box, shape, value)

    def __str__(self):
        return f'Region3(box={self.box}, shape={self.shape}, size={self.size})'

    core.use(None, 'region3_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.region3_save(self.handle, make_c_char_p(path))

    core.use(None, 'region3_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.region3_load(self.handle, make_c_char_p(path))

    core.use(c_double, 'region3_lrange', c_void_p, c_size_t)

    @property
    def box(self):
        """
        数据在三维空间内的范围，格式为：
            x0, y0, z0, x1, y1, z1
        其中 x0为x的最小值，x1为x的最大值; y和z类似
        """
        lr = [core.region3_lrange(self.handle, i) for i in range(3)]
        sh = self.shape
        sz = self.size
        rr = [lr[i] + sh[i] * sz[i] for i in range(3)]
        return lr + rr

    core.use(c_double, 'region3_shape', c_void_p, c_size_t)

    @property
    def shape(self):
        """
        返回每个网格在三个维度上的大小
        """
        return [core.region3_shape(self.handle, i) for i in range(3)]

    core.use(c_size_t, 'region3_size', c_void_p, c_size_t)

    @property
    def size(self):
        """
        返回三维维度上网格的数量<至少为1>
        """
        return [core.region3_size(self.handle, i) for i in range(3)]

    core.use(c_double, 'region3_get_center', c_void_p, c_size_t, c_size_t)
    core.use(None, 'region3_get_centers', c_void_p, c_void_p, c_void_p,
             c_void_p)

    def get_center(self, index=None, x=None, y=None, z=None):
        """
        给定格子的中心 <当index为None的时候，则返回所有的格子的中心，并作为Vector返回>
        """
        if index is not None:
            assert len(index) == 3
            return [core.region3_get_center(self.handle, index[i], i) for i in
                    range(3)]
        else:
            if not isinstance(x, Vector):
                x = Vector()
            if not isinstance(y, Vector):
                y = Vector()
            if not isinstance(z, Vector):
                z = Vector()
            core.region3_get_centers(self.handle, x.handle, y.handle, z.handle)
            return x, y, z

    core.use(None, 'region3_create', c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double)

    def create(self, box, shape, value=None):
        """
        创建网格. 其中box为即将划分网格的区域的范围，参考box属性的注释.
        shape为单个网格的大小(可以分别设置在三个维度上的尺寸)
        """
        assert len(box) == 6
        if not is_array(shape):
            shape = shape, shape, shape
        assert len(shape) == 3
        assert shape[0] > 0 and shape[1] > 0 and shape[2] > 0
        core.region3_create(self.handle, *box, *shape)
        if value is not None:
            self.fill(value)

    core.use(c_bool, 'region3_get', c_void_p, c_size_t, c_size_t, c_size_t)

    def get(self, index):
        """
        给定的格子是否是True
        """
        assert len(index) == 3
        return core.region3_get(self.handle, *index)

    core.use(None, 'region3_set', c_void_p, c_size_t, c_size_t, c_size_t,
             c_bool)

    def set(self, index, value):
        """
        给定的格子是否是True
        """
        assert len(index) == 3
        core.region3_set(self.handle, *index, value)

    core.use(None, 'region3_fill', c_void_p, c_bool)

    def fill(self, value):
        """
        设置所有的格子的数据
        """
        core.region3_fill(self.handle, value)

    core.use(None, 'region3_set_cube', c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double, c_bool,
             c_bool)

    def set_cube(self, box, value, inner=True):
        """
        将给定的六面体区域设置[内部]设置为value
        """
        assert len(box) == 6
        core.region3_set_cube(self.handle, *box, inner, value)

    def add_cube(self, box, inner=True):
        self.set_cube(box=box, value=True, inner=inner)

    def del_cube(self, box, inner=True):
        self.set_cube(box=box, value=False, inner=inner)

    core.use(None, 'region3_set_around_z', c_void_p, c_void_p, c_bool, c_bool)

    def set_around_z(self, z2r=None, z=None, r=None, value=True, inner=True):
        """
        设置环绕z的一个轴对称的区域
        """
        if not isinstance(z2r, Interp1):
            z2r = Interp1(x=z, y=r)
        core.region3_set_around_z(self.handle, z2r.handle, inner, value)

    core.use(c_bool, 'region3_contains', c_void_p, c_double, c_double, c_double)

    def contains(self, *args):
        """
        给定的点是否包含在此区域内<给定的参数为一个点在三维空间的坐标>
        """
        if len(args) == 3:
            pos = args
        else:
            assert len(args) == 1
            pos = args[0]
            assert len(pos) == 3
        return core.region3_contains(self.handle, *pos)

    core.use(None, 'region3_add_offset', c_void_p, c_double, c_double, c_double)

    def add_offset(self, dx, dy, dz):
        """
        添加一个平移
        """
        core.region3_add_offset(self.handle, dx, dy, dz)

    core.use(None, 'region3_clone', c_void_p, c_void_p)

    def clone(self, other):
        assert isinstance(other, Region3)
        core.region3_clone(self.handle, other.handle)

    core.use(None, 'region3_erase', c_void_p, c_void_p)

    def erase(self, other):
        assert isinstance(other, Region3)
        core.region3_erase(self.handle, other.handle)

    core.use(None, 'region3_get_inds', c_void_p, c_void_p)

    def get_indexes(self, buffer=None):
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        core.region3_get_inds(self.handle, buffer.handle)
        return buffer

    core.use(None, 'region3_print_top', c_void_p, c_char_p)

    def print_top(self, path):
        """
        将顶部一层的坐标打印到文件
        """
        if path is not None:
            core.region3_print_top(self.handle, make_c_char_p(path))


class ForceMap(HasHandle):
    """
    记录格子的受力 (用于dsmc). 必须依托于某一个格子才可以使用.
    """
    core.use(c_void_p, 'new_forcemap')
    core.use(None, 'del_forcemap', c_void_p)

    def __init__(self, handle=None, path=None):
        super(ForceMap, self).__init__(handle, core.new_forcemap,
                                       core.del_forcemap)
        if handle is None:
            if path is not None:
                self.load(path)

    core.use(None, 'forcemap_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.forcemap_save(self.handle, make_c_char_p(path))

    core.use(None, 'forcemap_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.forcemap_load(self.handle, make_c_char_p(path))

    core.use(None, 'forcemap_clear', c_void_p)

    def clear(self):
        core.forcemap_clear(self.handle)

    core.use(None, 'forcemap_clone', c_void_p, c_void_p)

    def clone(self, other):
        """
        从other中克隆数据，生成一个完全一样的拷贝
        """
        assert isinstance(other, ForceMap)
        core.forcemap_clone(self.handle, other.handle)

    def get_copy(self):
        """
        返回当前数据的拷贝
        """
        fmap = ForceMap()
        fmap.clone(self)
        return fmap

    core.use(None, 'forcemap_get_centers', c_void_p, c_void_p, c_void_p,
             c_void_p, c_void_p)

    def get_pos(self, reg3, x=None, y=None, z=None):
        """
        返回受力的点的位置
        """
        assert isinstance(reg3, Region3)
        if x is None:
            x = Vector()
        if y is None:
            y = Vector()
        if z is None:
            z = Vector()
        core.forcemap_get_centers(self.handle, reg3.handle, x.handle, y.handle,
                                  z.handle)
        return x, y, z

    core.use(None, 'forcemap_get_forces', c_void_p, c_void_p, c_void_p,
             c_void_p)

    def get_force(self, reg3, shear=None, normal=None):
        """
        返回受力的点的剪切力和法向应力
        """
        assert isinstance(reg3, Region3)
        if shear is None:
            shear = Vector()
        if normal is None:
            normal = Vector()
        core.forcemap_get_forces(self.handle, reg3.handle, shear.handle,
                                 normal.handle)
        return shear, normal

    core.use(None, 'forcemap_erode', c_void_p, c_void_p, c_void_p, c_double,
             c_void_p, c_double, c_size_t,
             c_double,
             c_void_p, c_void_p, c_void_p)

    def erode(self, reg3, strength, normal_weight=0, moles=None, dist=None,
              nmax=99999999,
              strength_modify_factor=0.5,
              vx=None, vy=None, vz=None):
        """
        土体侵蚀<并记录侵蚀发生的位置>
        todo:
            将erode函数修改为自由函数，而不再是这个类的成员函数
        """
        assert 0.0 <= strength_modify_factor <= 1.0
        assert isinstance(reg3, Region3), f'reg3={reg3}'
        assert isinstance(strength, Interp3), f'strength={strength}'
        hx = vx.handle if isinstance(vx, Vector) else 0
        hy = vy.handle if isinstance(vy, Vector) else 0
        hz = vz.handle if isinstance(vz, Vector) else 0
        if moles is not None and dist is not None:
            assert isinstance(moles, MoleVec)
            assert dist > 0
            core.forcemap_erode(self.handle, reg3.handle, strength.handle,
                                normal_weight,
                                moles.handle, dist, nmax,
                                strength_modify_factor,
                                hx, hy, hz)
        else:
            core.forcemap_erode(self.handle, reg3.handle, strength.handle,
                                normal_weight,
                                0, 0, nmax,
                                strength_modify_factor,
                                hx, hy, hz)


class Statistic(HasHandle):
    """
    分子数据统计.（用于dsmc）
    """
    core.use(c_void_p, 'new_stat')
    core.use(None, 'del_stat', c_void_p)

    def __init__(self, handle=None):
        super(Statistic, self).__init__(handle, core.new_stat, core.del_stat)

    core.use(None, 'stat_save', c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存. 可选扩展名:
            1: .txt  文本格式 (跨平台，基本不可读)
            2: .xml  xml格式 (具体一定可读性，体积最大，读写最慢，跨平台)
            3: .其它  二进制格式 (速度最快，体积最小，但Windows和Linux下生成的文件不能互相读取)
        """
        if path is not None:
            core.stat_save(self.handle, make_c_char_p(path))

    core.use(None, 'stat_load', c_void_p, c_char_p)

    def load(self, path):
        """
        序列化读取. 根据扩展名确定文件格式(txt, xml和二进制), 参考save函数
        """
        if path is not None:
            core.stat_load(self.handle, make_c_char_p(path))

    core.use(None, 'stat_update_vel', c_void_p, c_void_p, c_void_p, c_double)
    core.use(None, 'stat_update_vel_cylinder', c_void_p, c_void_p, c_void_p,
             c_double)

    def update_vel(self, lat, moles, relax_factor, cylinder=False):
        """
        更新各个格子内的速度; 如果cylinder为True，则首先对分子的速度进行转换：
            计算径向速度，并作为x分量；y分量设置为0；z分量维持不变
        然后再更新到格子；
        """
        assert isinstance(lat, Lattice3)
        assert isinstance(moles, MoleVec)
        if cylinder:
            core.stat_update_vel_cylinder(self.handle, lat.handle, moles.handle,
                                          relax_factor)
        else:
            core.stat_update_vel(self.handle, lat.handle, moles.handle,
                                 relax_factor)

    core.use(None, 'stat_get_vel', c_void_p, c_void_p, c_void_p, c_void_p)

    def get_vel(self, x=None, y=None, z=None):
        """
        返回中心的速度
        """
        if not isinstance(x, Vector):
            x = Vector()
        if not isinstance(y, Vector):
            y = Vector()
        if not isinstance(z, Vector):
            z = Vector()
        core.stat_get_vel(self.handle, x.handle, y.handle, z.handle)
        return x, y, z

    core.use(None, 'stat_update_den', c_void_p, c_void_p, c_void_p, c_double)
    core.use(None, 'stat_update_den_cylinder', c_void_p, c_void_p, c_void_p,
             c_double)

    def update_den(self, lat, moles, relax_factor, cylinder=False):
        """
        更新各个格子内的密度
        """
        assert isinstance(lat, Lattice3)
        assert isinstance(moles, MoleVec)
        if cylinder:
            core.stat_update_den_cylinder(self.handle, lat.handle, moles.handle,
                                          relax_factor)
        else:
            core.stat_update_den(self.handle, lat.handle, moles.handle,
                                 relax_factor)

    core.use(None, 'stat_get_den', c_void_p, c_void_p)

    def get_den(self, buffer=None):
        """
        返回密度
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.stat_get_den(self.handle, buffer.handle)
        return buffer

    core.use(None, 'stat_update_pre', c_void_p, c_void_p, c_void_p, c_double)
    core.use(None, 'stat_update_pre_cylinder', c_void_p, c_void_p, c_void_p,
             c_double)

    def update_pre(self, lat, moles, relax_factor, cylinder=False):
        """
        更新各个格子内的压力
        """
        assert isinstance(lat, Lattice3)
        assert isinstance(moles, MoleVec)
        if cylinder:
            core.stat_update_pre_cylinder(self.handle, lat.handle, moles.handle,
                                          relax_factor)
        else:
            core.stat_update_pre(self.handle, lat.handle, moles.handle,
                                 relax_factor)

    core.use(None, 'stat_get_pre', c_void_p, c_void_p)

    def get_pre(self, buffer=None):
        """
        返回压力
        """
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.stat_get_pre(self.handle, buffer.handle)
        return buffer


class Dsmc:
    core.use(c_size_t, 'dsmc_update_lat', c_void_p, c_void_p, c_double)
    core.use(c_size_t, 'dsmc_update_lat_tag', c_void_p, c_void_p, c_double,
             c_int)
    core.use(c_size_t, 'dsmc_update_lat_cylinder', c_void_p, c_void_p, c_double)

    @staticmethod
    def update_lattice(lat3, moles, lat_ratio=1.0, cylinder=False, tag=None):
        """
        更新网格上的分子。
        如果cylinder为True，则首先对分子的位置进行坐标变换：
            x：代表距离z轴的距离
            y：0
            z：z
        然后根据变换后的位置，将分子放入格子
        """
        assert isinstance(lat3, Lattice3)
        assert isinstance(moles, MoleVec)
        if tag is not None:
            assert not cylinder
            return core.dsmc_update_lat_tag(lat3.handle, moles.handle,
                                            lat_ratio, tag)
        if cylinder:
            return core.dsmc_update_lat_cylinder(lat3.handle, moles.handle,
                                                 lat_ratio)
        else:
            return core.dsmc_update_lat(lat3.handle, moles.handle, lat_ratio)

    core.use(None, 'dsmc_update_erosion_rate', c_void_p, c_void_p, c_void_p,
             c_void_p, c_double, c_double, c_double)

    @staticmethod
    @clock
    def update_erosion_rate(rate, reg3, fmap, strength, normal_weight,
                            relax_factor, rate_max):
        """
        根据受力，更新侵蚀速率. 不妨将这里的rate定义为侵蚀之后，每秒钟释放的粒子的数量.
        """
        assert isinstance(rate, Matrix3)
        assert isinstance(reg3, Region3)
        assert isinstance(fmap, ForceMap)
        assert isinstance(strength, Interp3)
        core.dsmc_update_erosion_rate(rate.handle, reg3.handle, fmap.handle,
                                      strength.handle,
                                      normal_weight, relax_factor, rate_max)

    core.use(c_double, 'dsmc_get_rate_template', c_void_p, c_void_p, c_void_p,
             c_void_p, c_double)

    @staticmethod
    @clock
    def get_rate_template(reg3: Region3, fmap: ForceMap, strength: Interp3,
                          normal_weight, buffer=None):
        """
        计算富裕出来的剪切力，并且存储到rate里面.
        """
        if not isinstance(buffer, Matrix3):
            buffer = Matrix3()
        q_sum = core.dsmc_get_rate_template(buffer.handle, reg3.handle,
                                            fmap.handle, strength.handle,
                                            normal_weight)
        return buffer, q_sum

    core.use(c_double, 'dsmc_get_shear_sum', c_void_p, c_void_p, c_void_p)

    @staticmethod
    @clock
    def get_shear_sum(rate: Matrix3, reg3: Region3, fmap: ForceMap):
        """
        返回fmap中所有的剪切力的累积值.
        """
        return core.dsmc_get_shear_sum(rate.handle, reg3.handle, fmap.handle)

    core.use(None, 'dsmc_add_particles', c_void_p, c_void_p, c_void_p, c_void_p,
             c_double,
             c_void_p, c_double)

    @staticmethod
    @clock
    def add_particles(moles, rate, reg3, fmap, dt, par, times=1.0):
        assert isinstance(moles, MoleVec)
        assert isinstance(rate, Matrix3)
        assert isinstance(reg3, Region3)
        assert isinstance(fmap, ForceMap)
        assert dt > 0
        assert isinstance(par, Molecule)
        assert par.tag < 0
        core.dsmc_add_particles(moles.handle, rate.handle, reg3.handle,
                                fmap.handle, dt, par.handle, times)

    core.use(None, 'dsmc_get_erosion_rate', c_void_p, c_void_p, c_void_p,
             c_void_p)

    @staticmethod
    @clock
    def get_erosion_rate(rate, fmap, reg3, buffer=None):
        """
        返回各个受力点的侵蚀速率
        """
        assert isinstance(rate, Matrix3)
        assert isinstance(reg3, Region3)
        assert isinstance(fmap, ForceMap)
        if not isinstance(buffer, Vector):
            buffer = Vector()
        core.dsmc_get_erosion_rate(buffer.handle, rate.handle, fmap.handle,
                                   reg3.handle)
        return buffer


if __name__ == '__main__':
    print(core.time_compile)
