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
"""
import importlib
import re
import warnings
from ctypes import c_uint

warnings.simplefilter("default")  # Default warning display

from zmlx.exts._utils import *
from zmlx.exts._dll import *
from zmlx.exts._timer import Timer, timer, clock
from zmlx.exts._ver import data_version
from zmlx.exts._str import String
from zmlx.exts._lic import lic
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
from zmlx.exts._sol import ConjugateGradientSolver
import zmlx.exts._utils as has_cells
from zmlx.exts._seepage import Seepage, Thermal, Reaction
from zmlx.exts._ip import InvasionPercolation
from zmlx.exts._frac import Dfn2, Lattice3, FracAlg, FractureNetwork, InfMatrix, DDMSolution2
import zmlx.exts._ip as ip

create_dict = dict


def feedback(text: str = 'feedback', subject: Optional[str] = None) -> bool:
    """向软件作者发送诊断信息用于产品改进。

    Args:
        text (str, optional): 反馈内容，默认为'feedback'
        subject (str, optional): 邮件主题，默认为None

    Returns:
        bool: 发送成功或禁用反馈时返回True，失败返回False

    Note:
        - 可通过设置环境变量disable_feedback='Yes'永久禁用
        - 实际发送使用sendmail函数实现
        - 默认收件人为zhangzhaobin@mail.iggcas.ac.cn
    """
    try:
        if app_data.getenv('disable_feedback', default='No',
                           ignore_empty=True) == 'Yes':
            return True
        else:
            return sendmail('zhangzhaobin@mail.iggcas.ac.cn',
                            subject=subject,
                            text=text,
                            name_from=None, name_to='Author')
    except:
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
    warnings.warn('This function will be removed after 2025-8-11',
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
            except:
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


def __feedback():
    """自动收集并反馈日志文件。

    该函数会检查日志文件夹中的日志文件，并将未反馈过的日志文件发送到指定邮箱。
    已反馈的日志文件会被标记，避免重复发送。

    Returns:
        None
    """
    try:
        folder_logs = app_data.root('logs')
        if not os.path.isdir(folder_logs):
            return
        folder_logs_feedback = app_data.root('logs_feedback')
        make_dirs(folder_logs_feedback)
        has_feedback = set(os.listdir(folder_logs_feedback))
        date = datetime.datetime.now().strftime("%Y-%m-%d.log")
        city = None
        for name in os.listdir(folder_logs):
            if name != date and name not in has_feedback:
                with open(os.path.join(folder_logs, name), 'r') as f1:
                    text = f1.read()
                    if city is None:
                        try:
                            from zmlx.alg.sys import get_city
                            city = f' from {get_city()}'
                        except:
                            city = ''
                    if feedback(text=text[0: 100000],
                                subject=f'log <{name}>{city}'):
                        with open(os.path.join(folder_logs_feedback, name),
                                  'w') as f2:
                            f2.write('\n')
    except:
        pass


try:
    if app_data.getenv('disable_auto_feedback', default='No',
                       ignore_empty=True) != 'Yes':
        __feedback()
except:
    pass

try:
    disable_timer = app_data.getenv(key='disable_timer', encoding='utf-8',
                                    default='No', ignore_empty=True)
    if disable_timer == 'Yes':
        timer.enabled(False)
        app_data.log(f'timer disabled')
except:
    pass

try:
    app_data.log(f'import zml <zml: v{version}, Python: {sys.version}>')
except:
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
    warnings.warn("is_chinese is deprecated (will be removed after 2027-4-14), use contain_chinese instead",
                  DeprecationWarning,
                  stacklevel=2)
    return contain_chinese(string)


class Alg:
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
        warnings.warn(
            'deprecated and will be removed after 2026-4-24. '
            'Use zmlx.alg.alpha.get_velocity_after_slowdown_by_viscosity instead.',
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


def main(argv: list):
    """
    模块运行的主函数.
    """
    if len(argv) == 1:
        print(about(check_lic=False))
        return
    if len(argv) == 2:
        if argv[1] == 'lic':
            print(lic.desc)
            return
        if argv[1] == 'env':
            try:
                from zmlx.alg.sys import install_dep
                install_dep(print)
            except Exception as e:
                print(e)
        return


class LazyImport:
    def __init__(self, module, name, deprecated_date=None):
        self.pack = module
        self.name = name
        self.date = deprecated_date

    def __get_origin(self):
        warnings.warn(
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
    'zmlx.utility.AttrKeys', 'add_keys', '2025-1-21')
AttrKeys = LazyImport(
    'zmlx.utility.AttrKeys', 'AttrKeys', '2025-1-21')
install = LazyImport(
    'zmlx.alg.install', 'install', '2025-1-21')
prepare_dir = LazyImport(
    'zmlx.filesys.prepare_dir', 'prepare_dir', '2025-1-21')
time2str = LazyImport(
    'zmlx.alg.time2str', 'time2str', '2025-1-21')
mass2str = LazyImport(
    'zmlx.alg.mass2str', 'mass2str', '2025-1-21')
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
    'zmlx.utility.Field', 'Field', '2025-1-21')

if __name__ == "__main__":
    main(sys.argv)
