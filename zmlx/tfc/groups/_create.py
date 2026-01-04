"""
实现对虚拟模型的分组，确保在一个分组内，模型并行执行的时候，不会出现数据的冲突.
"""
from typing import List, Set, Any, Dict, Optional, Tuple

from zmlx.exts import Seepage, get_index
from zmlx.tfc import seepage


def split(virtual_models: List[List[Any]]) -> List[List[int]]:
    """
    对虚拟模型进行分组，确保在一个分组内，模型并行执行的时候，不会出现数据的冲突.
    Args:
        virtual_models: 虚拟模型的列表。每一个虚拟模型，都是cell的列表.
    Returns:
        每一个分组内模型的ID的列表
    """

    # 分组后的每一个虚拟模型所在分组的ID
    group_ids = []

    # 每个Group内使用的cell的ID的集合
    cell_sets: List[Set[Any]] = []

    # 遍历已有的分组，当找到没有交集的分组时，就将该虚拟模型分到该分组
    for virtual_model in virtual_models:
        found_group = False
        for idx in range(len(cell_sets)):
            is_intersect = False
            for cell in virtual_model:
                if cell in cell_sets[idx]:
                    is_intersect = True
                    break
            if is_intersect:
                continue
            else:
                group_ids.append(idx)
                for cell in virtual_model:
                    cell_sets[idx].add(cell)
                found_group = True
                break
        if not found_group:
            group_ids.append(len(cell_sets))
            cell_sets.append(set(virtual_model))

    # 返回分组结果
    assert len(group_ids) == len(
        virtual_models), f"group_ids and virtual_models must have the same length, but got {len(group_ids)} and {len(virtual_models)}"

    res: List[List[int]] = []
    for idx in range(len(group_ids)):
        group_id = group_ids[idx]
        while group_id >= len(res):
            res.append([])
        assert group_id < len(res), f"group_id must be less than {len(res)}, but got {group_id}"
        res[group_id].append(idx)
    return res


def create_virtual_groups(
        real_models: List[Seepage],
        configs: List[Dict[str, Any]],
        model_template: Optional[Seepage] = None
) -> List[Dict[str, Any]]:
    """
    创建虚拟模型。这些模型不存储单元信息，而是依赖于copy_task来处理已有的模型.
    Args:
        real_models: 原始模型的列表.
        configs: 虚拟模型的建模数据列表
            对于每一个config，需要配置如下数据：
            cells: 如何构建一个cell. 每一个元素是一个字典，包含model_index和cell_index两个键。
            faces: 如何构建face, 每一个元素是一个字典，包含i0, i1, area, dist, perm, heat_cond
            injectors：如何构建注入点， 每一个元素是一个字典，包含fluid_name, rate, pos等键
        model_template: 虚拟模型的模板。 如果为None，会自动从models中获取第一个模型的模板。
    Returns:
        List[Dict[str, Any]]: 虚拟模型的列表，每个列表都是一个字典，包含models和copy_task两个键。
    """
    if len(real_models) == 0:
        return []

    if model_template is None:
        model_template = real_models[0].get_copy()
        model_template.clear_cells_and_faces()

    # 模型空间（临时的空间）
    virtual_model_spaces: List[Dict[str, Any]] = []

    for config in configs:
        assert isinstance(config, dict), f'config (type={type(config)}) is not a dict'

        cells: List[Dict[str, Any]] = config.get('cells', [])
        faces: List[Dict[str, Any]] = config.get('faces', [])
        if len(cells) == 0 or len(faces) == 0:
            continue

        # 创建模型
        virtual_model = model_template.get_copy()  # 拷贝基础模型参数
        source_ids: List[Tuple[Seepage, int]] = []
        target_ids: List[Tuple[Seepage, int]] = []
        cell_ids: List[Tuple[int, int]] = []  # 用于分区

        for c_data in cells:
            model_index = c_data.get('model_index')
            model_index = get_index(model_index, len(real_models))
            assert isinstance(model_index, int)
            assert 0 <= model_index < len(real_models)

            cell_index = c_data.get('cell_index')
            assert isinstance(cell_index, int)
            cell_data = real_models[model_index].get_cell(cell_index)
            assert cell_data is not None

            new_cell = virtual_model.add_cell(data=cell_data)
            source_ids.append((real_models[model_index], cell_data.index))
            cell_ids.append((model_index, cell_data.index))  # 用于分区
            target_ids.append((virtual_model, new_cell.index))

        for f_data in faces:
            i0 = f_data.get('i0')
            i1 = f_data.get('i1')
            assert isinstance(i0, int) and isinstance(i1, int)
            assert 0 <= i0 < virtual_model.cell_number
            assert 0 <= i1 < virtual_model.cell_number
            assert i0 != i1
            new_face = virtual_model.add_face(i0, i1)
            assert new_face is not None
            area = f_data.get('area', 1.0)
            dist = f_data.get('dist', 1.0)
            perm = f_data.get('perm', 0.0)
            heat_cond = f_data.get('heat_cond', 0.0)
            seepage.set_face(new_face, area=area, length=dist, perm=perm, heat_cond=heat_cond)

        # 设置注入点
        injectors: List[Dict[str, Any]] = config.get('injectors', [])

        if injectors is None:  # 防止准备数据的时候，将injectors设置为None
            injectors = []

        for inj in injectors:
            pos = inj.get('pos')
            if pos is None:
                continue
            assert isinstance(pos, (tuple, list)), f'pos {pos} is not a tuple or list'
            cell = virtual_model.get_nearest_cell(pos)
            if cell is None:
                continue
            fluid_name = inj.get('fluid_name')
            if fluid_name is None:
                continue

            assert isinstance(fluid_name, str)
            fid = virtual_model.find_fludef(name=fluid_name)
            assert fid is not None

            rate = inj.get('rate')
            if rate is None:
                continue

            assert isinstance(rate, (float, int)), f'rate {rate} is not a float or int'
            assert rate >= 0

            virtual_model.add_injector(
                fluid_id=fid[0],
                flu=cell.get_fluid(fid[0]),
                pos=cell.pos,
                radi=1.0,
                opers=[(0, rate)]
            )

        # 添加到列表中
        virtual_model_spaces.append(
            dict(model=virtual_model, source_ids=source_ids, target_ids=target_ids, cell_ids=cell_ids))

    if len(virtual_model_spaces) == 0:
        return []

    # 此时，创建了fracture_spaces，下面，要添加分组
    model_groups = split([space['cell_ids'] for space in virtual_model_spaces])

    groups = []
    for indexes in model_groups:
        assert isinstance(indexes, list)
        spaces: List[Dict[str, Any]] = [virtual_model_spaces[i] for i in indexes]
        # 模型
        real_models: List[Seepage] = [space['model'] for space in spaces]
        #
        source_ids: List[Tuple[Seepage, int]] = sum([space['source_ids'] for space in spaces], [])
        target_ids: List[Tuple[Seepage, int]] = sum([space['target_ids'] for space in spaces], [])
        copy_cells = seepage.create_copy_task(
            sources=[m.get_cell(i) for m, i in source_ids], targets=[m.get_cell(i) for m, i in target_ids]
        )
        groups.append({"models": real_models, "copy_cells": copy_cells})
    return groups
