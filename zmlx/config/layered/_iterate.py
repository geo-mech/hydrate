"""
将储层分为多个Seepage模型，并将这些模型分为多组。从整体上，会顺序地迭代每一组。然后在每一个组内，会并行地执行迭代。

整个模型用字典表示，包含如下键：
    groups: 分层模型的所有的层。每一个层都是一个字典，包含如下的key:
        copy_task (seepage.CellCopyTask, optional): 用于更新models，在迭代之后，输出models的数据
        models (list of Seepage): 该层的所有的 Seepage模型的列表.
        n_loop (int, optional): 迭代的循环次数, 会在每次迭代之后更新（仅仅用于输出）
    time: 当前的时间
    dt: 每次迭代对齐的时间步长. 必须设置大于0的值.
        注意，这并非每一个模型迭代的时候真实采用的dt,
        只不过是各个模型对齐时间的一个间隔.
    pool: 用于并行的线程池对象。 这个pool，一般不需要做特殊的设置。在迭代的时候，会自动创建一个pool.
"""
import warnings
from typing import Dict, Any, List, Optional

from zml import Seepage, ThreadPool
from zmlx.config import seepage


def get_models(group: Dict[str, Any]) -> List[Seepage]:
    """
    从配置中获取分层模型的所有的层，并执行必要的检查.
    如果配置中没有models键，返回空列表.
    Args:
        group: 分层模型的配置字典.

    Returns:
        List[Seepage]: 该层的所有的 Seepage模型的列表.
    """
    models = group.get('models')
    if models is None:
        group['models'] = []
        return group['models']

    # 执行必要的检查
    assert isinstance(models, list), "models must be a list of Seepage object"
    for model in models:
        assert isinstance(model, Seepage), "All models must be Seepage object"
        if not model.has_tag('check_dt'):
            warnings.warn(f"模型 {model} 没有 check_dt 标签", RuntimeWarning, stacklevel=2)

    # 返回列表
    return models


def iterate_group(group: Dict[str, Any], target_time, *, pool: Optional[ThreadPool] = None):
    """
    迭代一组模型。确保每个模型的时间，都推进到了target_time.
    同时，更新group中的n_loop键，记录迭代的循环次数。

    Args:
        group: 分层模型的配置字典.
        target_time: 目标时间.
        pool: 用于并行的线程池对象.
    Returns:
        None
    """
    models = get_models(group)
    if len(models) == 0:
        return

    # 复制cell的任务
    copy_cells = group.get('copy_cells')

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


def get_pool(space: Dict[str, Any]) -> ThreadPool:
    """
    返回用于并行的线程池对象。 如果space中没有pool键，会自动创建一个pool。
    Args:
        space: 整个模型的配置字典.
    Returns:
        ThreadPool: 用于并行的线程池对象.
    """
    pool = space.get('pool')
    if isinstance(pool, ThreadPool):
        return pool
    else:
        space['pool'] = ThreadPool()
        return space['pool']


def get_groups(space: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    返回分层模型的所有的层， 每一层都是一个字典， 包含models和copy_task两个键。
    如果space中没有groups键，返回空列表。
    Args:
        space: 整个模型的配置字典.
    Returns:
        List[Dict[str, Any]]: 分层模型的所有的层， 每一层都是一个字典， 包含models和copy_task两个键。
    """
    return space.get('groups', [])


def iterate(space: Dict[str, Any]):
    """
    对分层模型的每个层进行迭代。确保每个层的时间，都推进到了time+dt.
    然后，更新time标签，将时间推进到了time+dt.
    Args:
        space: 整个模型的配置字典.
    Returns:
        None
    """
    # 获取当前的时间time和时间步长dt
    time = space.get('time', 0.0)
    dt = space.get('dt', 0.0)  # 每次迭代对齐的时间步长
    if dt <= 0.0:
        warnings.warn("dt步长必须大于0", RuntimeWarning, stacklevel=2)
        return

    # 迭代的目标时间
    target_time = time + dt

    # 更新时间标签.
    space['time'] = target_time

    # 获取所有的层，并在各个层的内部进行迭代.
    for group in get_groups(space):
        assert isinstance(group, dict), "group must be a dict"
        iterate_group(group, target_time, pool=get_pool(space))
