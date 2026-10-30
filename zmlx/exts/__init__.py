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

# Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
import warnings
from ctypes import c_uint

from zmlx.system import log, warn

warnings.simplefilter("default")  # Default warning display

import zmlx.exts._ip as ip
import zmlx.exts._utils as has_cells
from zmlx.exts._ary import *
from zmlx.exts._coord import *
from zmlx.exts._dll import *
from zmlx.exts._dyn import *
from zmlx.exts._fmap import FileMap
from zmlx.exts._frac import (
    DDMSolution2,
    Dfn2,
    FracAlg,
    FractureNetwork,
    InfMatrix,
    Lattice3,
)
from zmlx.exts._hk import HasKeys
from zmlx.exts._interp import *
from zmlx.exts._ip import InvasionPercolation
from zmlx.exts._leq import get_default_solver_code, make_solver, set_default_solver_code
from zmlx.exts._lexpr import LinearExpr, create_lexpr
from zmlx.exts._lic import lic, web_license
from zmlx.exts._map import Map
from zmlx.exts._mat import *
from zmlx.exts._mesh import *
from zmlx.exts._pool import ThreadPool
from zmlx.exts._seepage import (
    Cell,
    CellData,
    Face,
    FaceData,
    FlowSol,
    FluData,
    FluDef,
    Fluid,
    Injector,
    Reaction,
    Seepage,
    Thermal,
    ThermalSol,
    calc_recommended_dt,
)
from zmlx.exts._sol import (
    BiCGSTABSolver,
    ConjugateGradientSolver,
    ICCGSolver,
    ILUBiCGSTABSolver,
    SimplicialLDLTSolver,
    SparseLUSolver,
)
from zmlx.exts._str import String
from zmlx.exts._tensor import *
from zmlx.exts._timer import Timer, clock, timer
from zmlx.exts._utils import *
from zmlx.exts._vec import *
from zmlx.exts._ver import data_version

# ⚠️ 2026-10-29 弃用：``version`` **已不是** ``_dll`` 的模块级定义，下面这个别名
#    只为「老路径不要断」而保留，**2027-10-29 删除**。内核版本（编译日期，六位
#    整数）请直接读 :attr:`core.version`。
#
#    ⚠️ 为什么要转发而不是直接让它消失：``version`` 原本是被
#       ``from zmlx.exts._dll import *`` 一起漏出来的，``zmlx/__init__.py`` 又接着
#       ``from zmlx.exts import *``，所以 ``zmlx.version`` / ``zmlx.exts.version``
#       在外部脚本里一直可见（``zmlx.ui.widgets.license_button`` 就曾用过）。
#       突然消失 = 属性不存在（AttributeError），而不是一句能读懂的提示。
#    ⚠️ 用**模块级** ``__getattr__``（PEP 562）而不是 ``version = core.version``：
#       后者在导入期就把值定死了，**每次读取**都发不出警告；而且会让这个别名
#       重新变成真名字，下一个人看不出它已弃用。


def __getattr__(name):
    """模块级惰性属性（PEP 562）：一批已弃用名字的转发。

    ``version`` 在这里**单独先处理**（它不是 import 来的，直接读内核）；其余名字
    统一查 :data:`_DEPRECATED`，由 :func:`_get_deprecated` 取值。

    ⚠️ 2026-10-29 起，其余这些名字原先都是 ``LazyImport`` 对象（各自带一个早就
    过期的弃用日期），现统一改由本函数惰性转发；**弃用日期沿用各自原值，不重新计时**。

    ⚠️ **``zmlx`` 顶层也有一份同名函数**（见 ``zmlx/__init__.py``），它用正常的
    ``getattr(zmlx.exts, name)`` 走**属性查找**转发到这里，**不直接调用本函数** ——
    直接调 ``__getattr__`` 会绕过「本模块确实没有该名字」这个前提（将来这里若真的
    加了一个同名属性，直接调用仍会返回映射表里的旧目标）。为了那种转发仍能把警告
    定位到用户那一行、文案里写出 ``zmlx.xxx``，本函数会**自己**看调用栈：
    若上一帧是 ``zmlx/__init__.py`` 的 ``__getattr__``，就把深度补 1、前缀换成
    ``'zmlx'``。这样两边没有私有参数约定，签名保持标准的 ``__getattr__(name)``。

    Args:
        name (str): 要取的属性名。

    Returns:
        ``version`` 返回内核的编译日期（``core.version``，六位整数，取不到为 ``None``）；
        其余名字返回 :data:`_DEPRECATED` 里登记的新位置的**真实对象**。

    Raises:
        AttributeError: ``name`` 既不是 ``version``，也不在 :data:`_DEPRECATED` 里。
    """
    stacklevel, prefix = _forwarded_from()
    if name == 'version':
        # 内核编译日期：不是 import 来的，`core` 就在本模块里，直接读。
        # ⚠️ 与 ``zmlx.__version__``（包版本）不是一个东西。
        if name not in _WARNED:
            _WARNED.add(name)
            warn(f'{prefix}.version is deprecated (will be removed after 2027-10-29), '
                 'use core.version instead (it is the KERNEL build date, not the '
                 'package version -- see zmlx.__version__ for that)',
                 DeprecationWarning, stacklevel=stacklevel)
        return core.version
    return _get_deprecated(name, stacklevel=stacklevel + 1, prefix=prefix)


def _forwarded_from():
    """判断本次属性读取是不是由 ``zmlx`` 顶层的 ``__getattr__`` 转下来的。

    Returns:
        tuple[int, str]: ``(stacklevel, prefix)``。直接从用户代码读
        ``zmlx.exts.xxx`` 时是 ``(2, 'zmlx.exts')``；经 ``zmlx/__init__.py``
        转发时是 ``(3, 'zmlx')``（多一跳，深度 +1；文案换成用户实际写的路径）。

    Note:
        判据是**上一帧的代码属于 ``zmlx/__init__.py`` 且函数名是 ``__getattr__``**，
        不依赖任何跨模块传入的私有参数。
    """
    import os
    import sys

    frame = sys._getframe(2)        # 调用 __getattr__ 的那一帧
    if frame is None:
        return 2, 'zmlx.exts'
    here = os.path.dirname(os.path.realpath(__file__))          # .../zmlx/exts
    top_init = os.path.join(os.path.dirname(here), '__init__.py')  # .../zmlx/__init__.py
    if (os.path.realpath(frame.f_code.co_filename) == os.path.realpath(top_init)
            and frame.f_code.co_name == '__getattr__'):
        return 3, 'zmlx'
    return 2, 'zmlx.exts'


def _get_deprecated(name, *, stacklevel, prefix):
    """取 :data:`_DEPRECATED` 里登记的已弃用名字，并发一条 ``DeprecationWarning``。

    只处理「转发到别处」的普通条目；``version`` 由 :func:`__getattr__` 先行处理。

    Args:
        name (str): 名字（必须是 :data:`_DEPRECATED` 的键）。
        stacklevel (int): 传给 :func:`zmlx.system.warn` 的栈深度 —— 让警告落在
            **真正调用方**那一行。``warn()`` 内部会再加 1。
        prefix (str): 警告文案里的旧路径前缀（``'zmlx.exts'`` / ``'zmlx'``），
            只为让提示里出现的是**用户实际写的**那个路径。

    Returns:
        目标对象：:data:`_DEPRECATED` 里登记的新位置的**真实对象**。

    Raises:
        AttributeError: ``name`` 没登记。
        ImportError: 目标模块或属性不存在 —— 说明映射表写错了，会立刻暴露在
            读取处，而不是等到调用时才炸。

    Note:
        - ⚠️ 同一个名字全进程只警告一次（见 :data:`_WARNED`）。三组原因：
          ① ``from zmlx import X`` 在 CPython 里会把 ``__getattr__`` 走**两次**
            （``_handle_fromlist`` + 模块本体），不去重就会并列两行一样的警告；
          ② 旧 ``LazyImport`` 是**每次调用**都警告，长循环里能刷屏；
          ③ 需求本来就只是「**是否**还在被用」，不是「用了多少次」。
        - ⚠️ 目标模块**按需**导入：只有真的取这个名字才会拉起它，
          所以 ``import zmlx`` 不会被这张表拖慢（保留了 ``LazyImport`` 的本意）。
    """
    spec = _DEPRECATED.get(name)
    if spec is None:
        raise AttributeError(f"module {prefix!r} has no attribute {name!r}")
    module, attr, date = spec
    if name not in _WARNED:
        _WARNED.add(name)
        warn(
            f"{prefix}.{name} is deprecated (will be removed after {date}), "
            f"please use <{module}.{attr}> instead.",
            DeprecationWarning,
            stacklevel=stacklevel,
        )
    return getattr(importlib.import_module(module), attr)


create_dict = dict


def feedback(text: str = "feedback", subject: Optional[str] = None) -> bool:
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
        if reply.strip().lower().startswith("the feedback was already sent recently"):
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


core.use(None, "set_srand", c_uint)


def set_srand(seed: int):
    """设置随机数生成器的种子。

    该函数用于设置随机数生成器的种子值，以确保随机数生成的可重复性。

    Args:
        seed (int): 随机数生成器的种子值，必须为无符号整数。

    Returns:
        None
    """
    core.set_srand(seed)


core.use(c_double, "get_rand")


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


core.use(None, "fetch_m", c_char_p)


def fetch_m(folder: Optional[str] = None):
    """获取预定义的 m 文件。

    这些 m 文件通常用于调试、绘图等场景。

    Args:
        folder (str): 存储 m 文件的文件夹路径。如果未提供，则使用默认路径。

    Warns:
        DeprecationWarning: 该函数将在 2025-8-11 之后被移除。
    """
    warn(
        "This function will be removed after 2025-8-11",
        DeprecationWarning,
        stacklevel=4,
    )
    if folder is None:
        core.fetch_m(make_c_char_p(""))
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


core.use(c_double, "test_loop", c_size_t, c_bool)


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
    info = f"Welcome to zml ({core.time_compile}; {core.compiler})"
    if check_lic:
        has_lic = lic.valid
    else:
        has_lic = True
    if not has_lic:
        author = "author (Email: zhangzhaobin@mail.iggcas.ac.cn, QQ: 542844710)"
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
    return dist**0.5


core.use(c_bool, "confuse_file", c_char_p, c_char_p, c_char_p, c_bool)


def confuse_file(
    ipath: str, opath: str, password: str, is_encrypt: bool = True
) -> bool:
    """对文件内容进行混淆加密或解密。

    Args:
        ipath (str): 输入文件路径。
        opath (str): 输出文件路径。
        password (str): 加密或解密的密码。
        is_encrypt (bool, optional): 是否进行加密。默认为 True，表示加密；False 表示解密。

    Returns:
        加密或解密的结果。
    """
    return core.confuse_file(
        make_c_char_p(ipath), make_c_char_p(opath), make_c_char_p(password), is_encrypt
    )


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
    disable_timer = app_data.getenv(
        key="disable_timer", encoding="utf-8", default="No", ignore_empty=True
    )
    if disable_timer == "Yes":
        timer.enabled(False)
        log("timer disabled", tag="timer disabled")
except Exception:  # noqa: BLE001
    pass

try:
    _msg = f"import zml <zml: v{core.version}, Python: {sys.version}>"
    log(_msg, tag=_msg)
except Exception:  # noqa: BLE001
    pass


def contain_chinese(string: str) -> bool:
    """检查字符串是否包含中文字符。

    Args:
        string (str): 待检查的字符串。

    Returns:
        bool: 如果字符串包含中文字符，则返回 True；否则返回 False。
    """
    return bool(re.search("[\u4e00-\u9fff]", string))


def is_chinese(string: str) -> bool:
    warn(
        "is_chinese is deprecated (will be removed after 2027-4-14), use contain_chinese instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return contain_chinese(string)


class Alg:
    """通用算法集合（C++ 静态方法绑定）。

    包含 link_point2、速度衰减计算、zml 头文件准备等工具方法。
    """

    core.use(None, "link_point2", c_void_p, c_void_p, c_double)

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

    core.use(
        c_double,
        "get_velocity_after_slowdown_by_viscosity",
        c_double,
        c_double,
        c_double,
    )

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
            "deprecated and will be removed after 2026-4-24. "
            "Use zmlx.algs.alpha.get_velocity_after_slowdown_by_viscosity instead.",
            DeprecationWarning,
            stacklevel=4,
        )
        return core.get_velocity_after_slowdown_by_viscosity(v0, a0, time)

    core.use(None, "prepare_zml", c_char_p, c_char_p, c_char_p)

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
        core.prepare_zml(
            make_c_char_p(code_path),
            make_c_char_p(target_folder),
            make_c_char_p(znetwork_folder),
        )


# ============================================================================
# 已弃用名字的映射表
# ============================================================================
#
# 格式：``旧名 -> (目标模块, 目标属性, 弃用日期)``。
# ``(None, None, 日期)`` 表示「不是 import 来的」，由 :func:`_get_deprecated`
# 单独处理（目前只有 ``version``）。
#
# ⚠️ **日期一栏照抄旧 ``LazyImport`` 的第三参数，不要改**：这批名字各自的弃用
#    日期是早就定下的（多数是 ``2025-1-21``），本次只是把实现从 ``LazyImport``
#    换成模块级 ``__getattr__``，**不重新计时**。新增条目才该写新日期。
# ⚠️ **本表位于文件末尾是必须的**：``__getattr__`` 只在「模块里找不到该名字」时才被
#    调用 —— 若这些名字仍在上方被赋值为真对象，``__getattr__`` 永远不会执行。
# ⚠️ 下列目标都是**核实过**的真实位置（2026-10-29 实测 ``hasattr`` 为 True）；
#    改这张表时务必同样核实，别照抄旧的 ``LazyImport`` 参数 —— 其中有 5 个原目标
#    模块已不存在，照抄会让调用方直接 ``ModuleNotFoundError``。
_DEPRECATED = {
    # —— ``version``：内核编译日期（六位 yymmdd），唯一入口是 ``core.version`` ——
    #    （它是本次新弃用的，所以日期与其余条目不同）
    # ⚠️ ``version`` **不在这张表里** —— 它在 __getattr__ 里单独处理。
    # —— 界面转发：目标全都还在，只是不该再从 ``exts`` 走（那会绕一圈） ——
    "information": ("zmlx.ui.gui_buffer", "information", "2025-1-21"),
    "question": ("zmlx.ui.gui_buffer", "question", "2025-1-21"),
    "plot": ("zmlx.ui.gui_buffer", "plot", "2025-1-21"),
    "gui": ("zmlx.ui.gui_buffer", "gui", "2025-1-21"),
    "break_point": ("zmlx.ui.gui_buffer", "break_point", "2025-1-21"),
    "breakpoint": (
        "zmlx.ui.gui_buffer",
        "break_point",
        "2025-1-21",
    ),  # 别名：同一个函数
    "gui_exec": ("zmlx.ui.gui_buffer", "gui_exec", "2025-1-21"),
    # —— 原 ``zmlx.filesys.*``（整个包 2026-4-15 已弃用），现统一在 ``zmlx.algs.fsys`` ——
    "time_string": ("zmlx.algs.fsys", "time_string", "2025-1-21"),
    "is_time_string": ("zmlx.algs.fsys", "is_time_string", "2025-1-21"),
    "has_tag": ("zmlx.algs.fsys", "has_tag", "2025-1-21"),
    "print_tag": ("zmlx.algs.fsys", "print_tag", "2025-1-21"),
    "first_only": ("zmlx.algs.fsys", "first_only", "2025-1-21"),
    "prepare_dir": ("zmlx.algs.fsys", "prepare_dir", "2025-1-21"),
    "make_fpath": ("zmlx.algs.fsys", "make_fpath", "2025-1-21"),
    "get_last_file": ("zmlx.algs.fsys", "get_last_file", "2025-1-21"),
    # —— 原目标模块**已不存在**（B 组），这里指向真实位置 ——
    "AttrKeys": (
        "zmlx.utils.attr_keys",
        "AttrKeys",
        "2025-1-21",
    ),  # 原 zmlx.utils.AttrKeys（模块没了；注意小写）
    "add_keys": (
        "zmlx.utils.attr_keys",
        "add_keys",
        "2025-1-21",
    ),  # 原 zmlx.utils.AttrKeys
    "install": (
        "zmlx.algs.sys",
        "pip_install",
        "2025-1-21",
    ),  # 原 zmlx.algs.install（该模块从未存在过）；顶层 `install` 也是 pip_install
    "time2str": (
        "zmlx.algs.base",
        "time2str",
        "2025-1-21",
    ),  # 原 zmlx.algs.time2str（模块没了）
    "mass2str": (
        "zmlx.algs.base",
        "mass2str",
        "2025-1-21",
    ),  # 原 zmlx.algs.mass2str（模块没了）
    "Field": (
        "zmlx.utils.fields",
        "Field",
        "2025-1-21",
    ),  # 原 zmlx.utils.Field（模块没了；注意复数）
    # —— 其余 ——
    "write_py": ("zmlx.io.python", "write_py", "2025-1-21"),
    "read_py": ("zmlx.io.python", "read_py", "2025-1-21"),
    "TherFlowConfig": ("zmlx.tfc.config", "TherFlowConfig", "2025-1-21"),
    "SeepageTher": (
        "zmlx.tfc.config",
        "SeepageTher",
        "2025-1-21",
    ),  # SeepageTher 与 TherFlowConfig 本就是**同一个类**（实测 is 为 True），
    # 这里显式写 SeepageTher 只是让意图更清楚，解析结果与 TherFlowConfig 完全相同
}


#: 已经警告过的**名字**，见 :func:`_warn_once`。
#:
#: ⚠️ 去重是**必需的**，不是优化，三组原因：
#:    ① ``from zmlx import X`` 在 CPython 里会把 ``__getattr__`` 走**两次**
#:       （``_handle_fromlist`` + 模块本体），不去重就会并列打出两行一样的警告；
#:    ② 旧 ``LazyImport`` 是**每次调用**都警告，仿真循环里能刷屏；
#:    ③ 需求本来就只是「**是否**还在被用」，不是「用了多少次」。
#: ⚠️ 键只用**名字**、不含文件与行号：``from`` 导入的「调用方行号」不稳定
#:    （见上，两条路径各报各的），拿它做键既不可靠也难解释。
#: ⚠️ 进程内有效、不落盘：跨进程 / 跨天的统计交给 :func:`zmlx.system.warn`
#:    的日志标签（``app_data.add_tag_today``，同一标签当天只记一次）。
_WARNED = set()
