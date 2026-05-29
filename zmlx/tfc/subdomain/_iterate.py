"""
将储层分为多个Seepage模型（子域），并将这些模型分为多组。从整体上，会顺序地迭代每一组。然后在每一个组内，会并行地执行迭代。

整个模型用字典表示，包含如下键：
    groups: 子域计算模型的所有的组。每一个组都是一个字典，包含如下的key:
        copy_task (seepage.CellCopyTask, optional): 用于更新models，在迭代之后，输出models的数据
        models (list of Seepage): 该组的所有的 Seepage模型的列表（每一个模型代表一个子域）.
        n_loop (int, optional): 迭代的循环次数, 会在每次迭代之后更新（仅仅用于输出）
    time: 当前的时间
    dt: 每次迭代对齐的时间步长. 必须设置大于0的值.
        注意，这并非每一个模型迭代的时候真实采用的dt,
        只不过是各个模型对齐时间的一个间隔.
    pool: 用于并行的线程池对象。 这个pool，一般不需要做特殊的设置。在迭代的时候，会自动创建一个pool.
"""
import warnings
from typing import Dict, Any, List, Optional

from zmlx.exts import Seepage, ThreadPool
from zmlx.tfc import seepage


def _get_models(group: Dict[str, Any]) -> List[Seepage]:
    """
    从分组配置中获取该分组下所有的子域模型。如果配置中没有models键，返回空列表.
    Args:
        group: 子域计算模型一个分组的配置字典.

    Returns:
        List[Seepage]: 该组的所有的子域(Seepage模型)的列表.
    """
    models: Optional[List[Seepage]] = group.get('models')
    if models is None:
        group['models'] = []
        return group['models']

    # 执行必要的检查
    assert isinstance(models, list), "models must be a list of Seepage object"
    for model in models:
        assert isinstance(model, Seepage), "All models must be Seepage object"
        if not model.has_tag('check_dt'):
            warnings.warn(f"模型 {model} 没有 check_dt 标签", RuntimeWarning, stacklevel=3)

    # 返回列表
    return models


def _iterate_group(group: Dict[str, Any], target_time, *, pool: Optional[ThreadPool] = None):
    """
    迭代子域计算模型中的一组子域。确保每个子域(Seepage模型)的时间，都推进到了target_time.
    同时，更新group中的n_loop，记录迭代的循环次数。

    Args:
        group: 子域计算模型中一个分组的配置字典.
        target_time: 目标时间.
        pool: 用于并行的线程池对象.
    Returns:
        None
    """
    models: List[Seepage] = _get_models(group)
    if len(models) == 0:
        return

    # 复制cell的任务
    copy_cells: Optional[seepage.CellCopyTask] = group.get('copy_cells')

    # 将数据拷贝到虚拟模型中
    if copy_cells is not None:
        assert isinstance(copy_cells, seepage.CellCopyTask), "copy_cells must be a seepage.CellCopyTask object"
        copy_cells(True)

    # 迭代所有的模型到目标时间
    n_loop, n_iter = seepage.iterate_until(*models, pool=pool, target_time=target_time)

    # 尝试迭代dt所需要的循环的次数
    group['n_loop'] = n_loop

    # 再将数据拷贝回来 （从虚拟模型到原始模型）
    if copy_cells is not None:
        assert isinstance(copy_cells, seepage.CellCopyTask), "copy_cells must be a seepage.CellCopyTask object"
        copy_cells(False)


def _get_pool(space: Dict[str, Any]) -> Optional[ThreadPool]:
    """
    返回用于并行的线程池对象。 如果subdomain_model中没有pool键，会自动创建一个pool。
    Args:
        space: 子域计算模型的配置字典.
    Returns:
        Optional[ThreadPool]: 用于并行的线程池对象.
    """
    pool = space.get('pool')
    if isinstance(pool, ThreadPool):
        return pool
    elif pool is None:
        space['pool'] = ThreadPool()
        return space['pool']
    else:
        return None


def _get_groups(space: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    返回子域计算模型的所有的分组， 每一组都是一个字典， 包含models和copy_task两个键。
    如果subdomain_model中没有groups键，返回空列表。
    Args:
        space: 整个子域计算模型的配置字典.
    Returns:
        List[Dict[str, Any]]: 子域计算模型的所有的分组， 每一组都是一个字典， 包含models和copy_task两个键。
    """
    res = space.get('groups')
    if res is None:
        space['groups'] = []
        return space['groups']

    assert isinstance(res, list), f"groups must be a list of dict, but got {type(res)}"
    for item in res:
        assert isinstance(item, dict), "group must be a dict"
    return res


def iterate(space: Dict[str, Any]):
    """
    迭代子域计算模型：向前迭代一步，确保每个分组中，每一个子域模型的时间，都推进到了time+dt.
    然后，更新time标签，将时间推进到了time+dt.
    Args:
        space: 子域计算模型的配置字典. 包含groups, time, dt, pool等键.
               其中，groups是子域计算模型的所有的分组，每个分组都是一个字典，包含models和copy_task等键。
                    dt是各个分组中所有的模型对齐的时间，并非真实采用的步长
    Notes:
        此函数会按照顺序迭代每个分组的模型.
        (在每个分组内部，先运行copy_task，再<并行地>迭代所有模型(即子域)，然后在运行反向的copy_task).
    Returns:
        None
    """
    # 获取当前的时间time和时间步长dt
    time: float = space.get('time', 0.0)
    if time <= 0.0:
        time = 0.0

    dt: float = space.get('dt', 0.0)  # 每次迭代对齐的时间步长
    if dt <= 0.0:
        warnings.warn("dt步长必须大于0", RuntimeWarning, stacklevel=2)
        return

    # 迭代的目标时间
    target_time = time + dt

    # 更新时间标签.
    space['time'] = target_time

    # 获取所有的组，并在各个组的内部进行迭代.
    for group in _get_groups(space):
        assert isinstance(group, dict), "group must be a dict"
        _iterate_group(group, target_time, pool=_get_pool(space))
