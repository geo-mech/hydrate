# -*- coding: utf-8 -*-
"""
描述: 流体-传热-化学-应力计算的核心模块；
      C++代码的Python接口（必须与 zml.dll一起使用）。

环境: Windows 10/11；Python 3.7或更高版本；64位系统；
     注：
     另有Linux版本，如有必要可联系作者获取。

依赖: 部分功能依赖 numpy/scipy/matplotlib等.

网站: https://gitee.com/geomech/hydrate;
    注:
    在使用过程中遇到问题，优先在此页面"新建Issue"来反馈.

作者: 张召彬 <zhangzhaobin@mail.iggcas.ac.cn>，
     中国科学院地质与地球物理研究所.

Modified by Claude, 2026-08-12
"""

import datetime
import importlib
import re
import sys
from zmlx.system import log, warn
# Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
import warnings
from ctypes import c_uint

warnings.simplefilter("default")  # Default warning display

from zmlx.exts._utils import *
from zmlx.exts._dll import *
from zmlx.exts._timer import Timer, timer, clock
from zmlx.exts._ver import data_version
from zmlx.exts._str import String
from zmlx.exts._lic import lic, web_license
from zmlx.exts._pool import ThreadPool
from zmlx.exts._fmap import FileMap
from zmlx.exts._vec import *
from zmlx.exts._map import Map
from zmlx.exts._ary import *
from zmlx.exts._tensor import *
from zmlx.exts._coord import *
from zmlx.exts._interp import *
from zmlx.exts._mat import *
from zmlx.exts._mesh import *
from zmlx.exts._lexpr import LinearExpr, create_lexpr
from zmlx.exts._dyn import *
from zmlx.exts._sol import (ConjugateGradientSolver, SparseLUSolver,
                            SimplicialLDLTSolver, BiCGSTABSolver,
                            ICCGSolver, ILUBiCGSTABSolver)
from zmlx.exts._hk import HasKeys
import zmlx.exts._utils as has_cells
from zmlx.exts._seepage import (
    Seepage, Thermal, Reaction, FluDef, FluData, Fluid, CellData, Cell, FaceData, Face, Injector, FlowSol, ThermalSol,
    calc_recommended_dt
)
from zmlx.exts._ip import InvasionPercolation
from zmlx.exts._frac import Dfn2, Lattice3, FracAlg, FractureNetwork, InfMatrix, DDMSolution2
import zmlx.exts._ip as ip
from zmlx.exts._leq import get_default_solver_code, set_default_solver_code, make_solver

create_dict = dict


def feedback(text: str = 'feedback', subject: Optional[str] = None) -> bool:
    """向软件作者发送诊断信息用于产品改进。

    走服务端接口 ``web_license.feedback``：机器码由 C++ 侧自己算。

    ⚠️ **不再有直连 SMTP 的兜底路径**：机器没授权时也能提交反馈，但接口本身
    **不可用**（没有 DLL，或这一版没有该导出）时直接返回 False —— 那种情况下
    改用服务端代发（``web_license.mail``）同样发不出去：它依赖同一个 DLL，门槛
    还更高（要求已注册且授权有效）。详见 ``zmlx.system.sendmail``。

    ⚠️ **不在本地预判「接口可不可用」**：``web_license`` 的公开方法本来就承诺
    **不抛异常、一切失败都以一句文本返回**，那些描述**不以任何成功记号开头**，
    走到下面同样得到 False —— 判据只留一处，两边不会漂。

    Args:
        text (str, optional): 反馈内容，默认为'feedback'
        subject (str, optional): [已忽略] 服务端接口没有「主题」字段，
            保留参数只为兼容旧签名。

    Returns:
        bool: 确实发出去了（或服务端答「刚发过」）返回True；失败、
            接口不可用、以及**反馈被禁用**时返回 False

    Note:
        - 可通过设置环境变量disable_feedback='Yes'永久禁用。⚠️ 禁用时返回
          **False**（不是 True）：语义是「这次没有发送」，调用方据此不会把
          日志标记成「已反馈」
    """
    try:
        if (
            app_data.getenv("disable_feedback", default="No", ignore_empty=True)
            == "Yes"
        ):
            return False

        # ⚠️ **不在这里预判「接口可不可用」**：``web_license`` 的**公开方法**
        #    本来就承诺「不抛异常、失败以一句文本返回」，那些描述都不以成功
        #    记号开头，照样走 return False。
        #    外部调用 ``web_license`` 请**只用它的公开方法**，别再摸 ``core``。
        reply = str(web_license.feedback(text) or "")
        # ⚠️ 成功记号是 'Succeed'（不是 'Yes'）。判定只看开头 7 个字符：
        #    超长时服务端会在成功记号后追加截断说明段，不能整串比较。
        #    本判定**本地实现**（_lic 只留 License / lic / WebLicense /
        #    web_license，不再提供判定函数）。
        if str(reply).strip()[:7].lower() == "succeed":
            return True
        # 限流不算失败：这段内容确实已经发出去过了。
        # ⚠️ 返回 True 是有意的：调用方（`zmlx` 导入时的自动反馈）把它当作「这文件不用再发」
        #    的标记，返回 False 会让它反复撞限流。
        if reply.strip().lower().startswith(
            "the feedback was already sent recently"
        ):
            return True
        print(f"feedback rejected: {reply}")
        return False
    except Exception:
        return False


def get_file() -> str:
    """获取当前执行文件的绝对路径。

    Returns:
        str: 当前Python文件的完整路径

    Note:
        - 等价于 os.path.realpath(__file__)
        - 支持符号链接解析
        - 结果包含文件名和扩展名
    """
    return os.path.realpath(__file__)


def get_dir() -> str:
    """获取当前执行文件所在目录的绝对路径。

    Returns:
        str: 当前文件所在目录的完整路径

    Note:
        - 等价于 os.path.dirname(os.path.realpath(__file__))
        - 常用于动态加载库时的路径定位
        - 结果不包含末尾路径分隔符
    """
    return os.path.dirname(os.path.realpath(__file__))


core.use(None, 'set_srand', c_uint)


def set_srand(seed: int):
    """设置随机数生成器的种子。

    该函数用于设置随机数生成器的种子值，以确保随机数生成的可重复性。

    Args:
        seed (int): 随机数生成器的种子值，必须为无符号整数。

    Returns:
        None
    """
    core.set_srand(seed)


core.use(c_double, 'get_rand')


def get_rand() -> float:
    """生成一个 0 到 1 之间的随机数。

    该函数返回一个均匀分布在 [0, 1) 区间内的随机浮点数。

    Returns:
        float: 一个 0 到 1 之间的随机浮点数。
    """
    return core.get_rand()


def get_time_compile() -> str:
    """获取编译时间。

    Returns:
        str: 用字符串表示的编译的时间
    """
    return core.time_compile


def run(fn: Callable) -> Any:
    """运行需要调用内存的代码，并检查错误。

    Args:
        fn: 需要运行的函数或代码。

    Returns:
        运行结果。
    """
    return core.run(fn)


core.use(None, 'fetch_m', c_char_p)


def fetch_m(folder: Optional[str] = None):
    """获取预定义的 m 文件。

    这些 m 文件通常用于调试、绘图等场景。

    Args:
        folder (str): 存储 m 文件的文件夹路径。如果未提供，则使用默认路径。

    Warns:
        DeprecationWarning: 该函数将在 2025-8-11 之后被移除。
    """
    warn('This function will be removed after 2025-8-11',
                  DeprecationWarning, stacklevel=2)
    if folder is None:
        core.fetch_m(make_c_char_p(''))
    else:
        assert isinstance(folder, str)
        core.fetch_m(make_c_char_p(folder))


def reg(code: Optional[str] = None) -> Optional[str]:
    """注册或获取本机序列号。

    当 `code` 为 None 时，返回本机的序列号。
    如果 `code` 为字符串的时候，将首先长度将code视为授权数据，失败的时候，
    再将其视为序列号并生成授权数据

    Args:
        code (str, optional): 序列号或授权数据。默认为 None。

    Returns:
        str: 本机序列号或生成的授权数据。
    """
    if code is None:
        return lic.usb_serial
    else:
        if isinstance(code, str):
            try:
                if len(code) > 0:
                    return lic.load(code)
                else:
                    return None
            except Exception:
                if lic.is_admin and len(code) > 0:
                    return lic.create(code)
                else:
                    return None
        else:
            return None


core.use(c_double, 'test_loop', c_size_t, c_bool)


def test_loop(count: int, parallel: bool = True) -> float:
    """测试内核中指定长度的循环并返回耗时。

    Args:
        count (int): 循环次数。
        parallel (bool, optional): 是否并行执行。默认为 True。

    Returns:
        float: 测试耗时。
    """
    return core.test_loop(count, parallel)


def about(check_lic: bool = True) -> str:
    """返回模块信息。

    Args:
        check_lic (bool, optional): 是否检查授权状态。默认为 True。

    Returns:
        str: 模块信息及授权状态提示。
    """
    info = f'Welcome to zml ({core.time_compile}; {core.compiler})'
    if check_lic:
        has_lic = lic.valid
    else:
        has_lic = True
    if not has_lic:
        author = 'author (Email: zhangzhaobin@mail.iggcas.ac.cn, QQ: 542844710)'
        info = f"""{info}. 

Note: license not found, please send 
    1. hardware info: "{lic.usb_serial}" 
    2. Your name, workplace, and contact information 

to {author}"""
    return info


def get_norm(p):
    """计算点到原点的距离。

    Args:
        p (list or tuple): 点的坐标。

    Returns:
        float: 点到原点的距离。
    """
    dist = 0.0
    for dim in range(len(p)):
        dist += p[dim] ** 2
    return dist ** 0.5


core.use(c_bool, 'confuse_file',
         c_char_p, c_char_p, c_char_p, c_bool)


def confuse_file(ipath: str, opath: str, password: str, is_encrypt: bool = True) -> bool:
    """对文件内容进行混淆加密或解密。

    Args:
        ipath (str): 输入文件路径。
        opath (str): 输出文件路径。
        password (str): 加密或解密的密码。
        is_encrypt (bool, optional): 是否进行加密。默认为 True，表示加密；False 表示解密。

    Returns:
        加密或解密的结果。
    """
    return core.confuse_file(make_c_char_p(ipath), make_c_char_p(opath),
                             make_c_char_p(password), is_encrypt)


def get_average_perm(p0, p1, get_perm, sample_dist=None, depth=0):
    """计算两点之间的平均渗透率或平均导热率。

    注意：该函数仅用于计算平均渗透率，考虑了串联效应。

    Args:
        p0 (list or tuple): 第一个点的坐标。
        p1 (list or tuple): 第二个点的坐标。
        get_perm: 获取渗透率或导热率的函数。
        sample_dist (float, optional): 采样距离。默认为 None。
        depth (int, optional): 递归深度。默认为 0。

    Returns:
        float: 两点之间的平均渗透率或导热率。
    """
    pos = [(p0[i] + p1[i]) / 2 for i in range(len(p0))]
    dist = get_distance(p0, p1)
    if sample_dist is None or depth >= 4 or sample_dist >= dist:
        k = get_perm(*pos)
        if isinstance(k, Tensor3):
            assert len(p0) == 3 and len(p1) == 3
            k = k.get_along([p1[i] - p0[i] for i in range(3)])
            return max(k, 0.0)
        else:
            return max(k, 0.0)
    k1 = get_average_perm(p0, pos, get_perm, sample_dist, depth + 1)
    k2 = get_average_perm(p1, pos, get_perm, sample_dist, depth + 1)
    return k1 * k2 * 2.0 / (k1 + k2)


# ⚠️ 原先这里有一段 `__feedback()`：导入 exts 时自动收集并提交历史日志。
#    2026-10-17 已**整段移到 `zmlx/__init__.py` 底部**（用户要求：导入 zmlx 时执行）。
#    理由不只是「触发时机」—— exts 是 DLL 绑定层（第 1 层），不该在导入期做
#    「读文件 + 联网提交」这类应用级副作用；包入口的底部才是「整个 zmlx 已就绪」那一刻。
#    行为一字未改：只提交**非当天**且未反馈过的日志，开关仍是 `disable_auto_feedback`。

try:
    disable_timer = app_data.getenv(key='disable_timer', encoding='utf-8',
                                    default='No', ignore_empty=True)
    if disable_timer == 'Yes':
        timer.enabled(False)
        log('timer disabled', tag='timer disabled')
except Exception:
    pass

try:
    _msg = f'import zml <zml: v{version}, Python: {sys.version}>'
    log(_msg, tag=_msg)
except Exception:
    pass


def contain_chinese(string: str) -> bool:
    """检查字符串是否包含中文字符。

    Args:
        string (str): 待检查的字符串。

    Returns:
        bool: 如果字符串包含中文字符，则返回 True；否则返回 False。
    """
    return bool(re.search('[\u4e00-\u9fff]', string))


def is_chinese(string: str) -> bool:
    warn("is_chinese is deprecated (will be removed after 2027-4-14), use contain_chinese instead",
                  DeprecationWarning,
                  stacklevel=2)
    return contain_chinese(string)


class Alg:
    """通用算法集合（C++ 静态方法绑定）。

    包含 link_point2、速度衰减计算、zml 头文件准备等工具方法。
    """

    core.use(None, 'link_point2',
             c_void_p, c_void_p, c_double)

    @staticmethod
    def link_point2(points, lmax):
        """
        在二维点集之间建立连接关系。

        Args:
            points (Vector): 包含二维坐标点的向量，格式为[x0, y0, x1, y1,...]
            lmax (float): 允许建立连接的最大距离阈值

        Returns:
            UintVector: 包含连接索引的列表，格式为[起点0, 终点0, 起点1, 终点1,...]

        Raises:
            AssertionError: 当points参数不是Vector类型时抛出
        """
        assert isinstance(points, Vector)
        lnks = UintVector()
        core.link_point2(lnks.handle, points.handle, lmax)
        return lnks

    core.use(c_double, 'get_velocity_after_slowdown_by_viscosity',
             c_double,
             c_double, c_double)

    @staticmethod
    def get_velocity_after_slowdown_by_viscosity(v0, a0, time):
        """
        计算粘性流体中物体速度随时间的变化。

        Args:
            v0 (float): 初始速度（m/s）
            a0 (float): 初始时刻由粘性阻力产生的加速度（m/s²），方向与速度相反
            time (float): 经过的时间（秒）

        Returns:
            float: 指定时间后的物体速度（m/s）

        Note:
            基于粘性阻力与速度成正比的假设，使用指数衰减模型计算
        """
        warn(
            'deprecated and will be removed after 2026-4-24. '
            'Use zmlx.algs.alpha.get_velocity_after_slowdown_by_viscosity instead.',
            DeprecationWarning, stacklevel=2)
        return core.get_velocity_after_slowdown_by_viscosity(
            v0, a0, time)

    core.use(None, 'prepare_zml',
             c_char_p, c_char_p, c_char_p)

    @staticmethod
    def prepare_zml(code_path, target_folder, znetwork_folder):
        """
        准备ZML库的头文件到指定目录。

        Args:
            code_path (str): 需要监测的C++源代码目录路径
            target_folder (str): 目标输出目录，用于存放生成的zml头文件
            znetwork_folder (str): ZNetwork库的源代码目录路径

        Returns:
            None

        Note:
            该操作会覆盖目标目录中已存在的同名文件
        """
        core.prepare_zml(make_c_char_p(code_path),
                         make_c_char_p(target_folder),
                         make_c_char_p(znetwork_folder))


class LazyImport:
    """延迟导入包装器（按需加载模块属性）。"""

    def __init__(self, module, name, deprecated_date=None):
        """初始化延迟导入。

        Args:
            module: 目标模块名。
            name: 目标属性名。
            deprecated_date: 弃用日期（可选）。
        """
        self.pack = module
        self.name = name
        self.date = deprecated_date

    def __get_origin(self):
        warn(
            f'function in zml will be removed after {self.date}, '
            f'please use <{self.pack}.{self.name}> instead.',
            DeprecationWarning,
            stacklevel=3
        )
        mod = importlib.import_module(self.pack)
        return getattr(mod, self.name, None)

    def __call__(self, *args, **kwargs):
        return self.__get_origin()(*args, **kwargs)

    def __getattr__(self, *args, **kwargs):
        return getattr(self.__get_origin(), *args, **kwargs)


information = LazyImport(
    'zmlx.ui.gui_buffer', 'information', '2025-1-21')
question = LazyImport(
    'zmlx.ui.gui_buffer', 'question', '2025-1-21')
plot = LazyImport(
    'zmlx.ui.gui_buffer', 'plot', '2025-1-21')
gui = LazyImport(
    'zmlx.ui.gui_buffer', 'gui', '2025-1-21')
break_point = LazyImport(
    'zmlx.ui.gui_buffer', 'break_point', '2025-1-21')
breakpoint = LazyImport(
    'zmlx.ui.gui_buffer', 'break_point', '2025-1-21')
gui_exec = LazyImport(
    'zmlx.ui.gui_buffer', 'gui_exec', '2025-1-21')
time_string = LazyImport(
    'zmlx.filesys.tag', 'time_string', '2025-1-21')
is_time_string = LazyImport(
    'zmlx.filesys.tag', 'is_time_string', '2025-1-21')
has_tag = LazyImport(
    'zmlx.filesys.tag', 'has_tag', '2025-1-21')
print_tag = LazyImport(
    'zmlx.filesys.tag', 'print_tag', '2025-1-21')
first_only = LazyImport(
    'zmlx.filesys.first_only', 'first_only', '2025-1-21')
add_keys = LazyImport(
    'zmlx.utils.AttrKeys', 'add_keys', '2025-1-21')
AttrKeys = LazyImport(
    'zmlx.utils.AttrKeys', 'AttrKeys', '2025-1-21')
install = LazyImport(
    'zmlx.algs.install', 'install', '2025-1-21')
prepare_dir = LazyImport(
    'zmlx.filesys.prepare_dir', 'prepare_dir', '2025-1-21')
time2str = LazyImport(
    'zmlx.algs.time2str', 'time2str', '2025-1-21')
mass2str = LazyImport(
    'zmlx.algs.mass2str', 'mass2str', '2025-1-21')
make_fpath = LazyImport(
    'zmlx.filesys.make_fpath', 'make_fpath', '2025-1-21')
get_last_file = LazyImport(
    'zmlx.filesys.get_last_file', 'get_last_file', '2025-1-21')
write_py = LazyImport(
    'zmlx.io.python', 'write_py', '2025-1-21')
read_py = LazyImport(
    'zmlx.io.python', 'read_py', '2025-1-21')
TherFlowConfig = LazyImport(
    'zmlx.config.TherFlowConfig', 'TherFlowConfig', '2025-1-21')
SeepageTher = LazyImport(
    'zmlx.config.TherFlowConfig', 'TherFlowConfig', '2025-1-21')
Field = LazyImport(
    'zmlx.utils.Field', 'Field', '2025-1-21')
