"""
实现对虚拟模型的分组，确保在一个分组内，模型并行执行的时候，不会出现数据的冲突.
"""
from typing import List, Set, Any


def group(virtual_models: List[List[Any]]) -> List[List[int]]:
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


def test_1():
    import random

    all_cells = [(i, j) for i in range(20) for j in range(5)]
    virtual_models = [
        random.sample(all_cells, 5) for _ in range(100)
    ]
    for g in group(virtual_models):
        print(g)


if __name__ == '__main__':
    test_1()
