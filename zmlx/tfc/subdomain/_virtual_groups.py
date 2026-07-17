from typing import List, Any, Dict, Optional, Tuple

from zmlx.exts import Seepage, get_index
from zmlx.tfc import seepage
from zmlx.tfc.subdomain._model import create_group
from zmlx.tfc.subdomain._split import split


def create_virtual_groups(
        real_models: List[Seepage],
        configs: List[Dict[str, Any]],
        model_template: Optional[Seepage] = None
) -> List[Dict[str, Any]]:
    """
    创建虚拟模型。这些模型不存储单元信息，而是依赖于cell_copy来处理已有的模型.
    Args:
        real_models: 原始模型的列表.
        configs: 虚拟模型的建模数据列表
            对于每一个config，需要配置如下数据：
            cells: 如何构建一个cell. 每一个元素是一个字典，包含model_index和cell_index两个键。
            faces: 如何构建face, 每一个元素是一个字典，包含i0, i1, area, dist, perm, heat_cond
            injectors：如何构建注入点， 每一个元素是一个字典，包含fluid_name, rate, pos等键
        model_template: 虚拟模型的模板。 如果为None，会自动从models中获取第一个模型的模板。
    Returns:
        List[Dict[str, Any]]: 虚拟模型的列表，每个列表都是一个字典，包含models和cell_copy两个键。
    """
    if len(real_models) == 0:
        return []

    if model_template is None:  # 默认使用第一个模型作为模板
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

        for inj in injectors:  # 这里对于injectors的设置比较有限，如果需要更复杂的设置，需要在创建之后，去进一步设置
            pos = inj.get('pos')
            if pos is None:
                continue
            assert isinstance(pos, (tuple, list)), f'pos {pos} is not a tuple or list'
            assert len(pos) == 3, f'pos {pos} must have 3 elements'

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
            dict(model=virtual_model, source_ids=source_ids, target_ids=target_ids, cell_ids=cell_ids)
        )

    if len(virtual_model_spaces) == 0:
        return []

    # 此时，创建了fracture_spaces，下面，要添加分组
    model_groups = split([space['cell_ids'] for space in virtual_model_spaces])

    groups = []
    for indexes in model_groups:
        assert isinstance(indexes, list)  # 此时，indexes是virtual_model_spaces中的索引
        spaces: List[Dict[str, Any]] = [virtual_model_spaces[i] for i in indexes]
        # 模型（前面创建的virtual_model）
        models: List[Seepage] = [space['model'] for space in spaces]
        # 创建复制任务
        source_ids: List[Tuple[Seepage, int]] = sum([space['source_ids'] for space in spaces], [])
        target_ids: List[Tuple[Seepage, int]] = sum([space['target_ids'] for space in spaces], [])
        cell_copy = seepage.create_copy_task(
            sources=[m.get_cell(i) for m, i in source_ids], targets=[m.get_cell(i) for m, i in target_ids]
        )
        groups.append(create_group(models, cell_copy))
    return groups
