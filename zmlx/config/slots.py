# 一些预定义函数
standard_slots = {'print': print}


def get_slots(slots=None):
    """
    返回包含standard_slots在内的槽函数
    """
    results = standard_slots.copy()
    if slots is not None:
        results.update(slots)
    return results


def get_slot(name, extra_slots=None):
    """
    返回给定名字的slot. 并且，如果给定的slots中不存在，则搜索标准的slots
    """
    if name is None:
        return None
    if extra_slots is not None:
        func = extra_slots.get(name)
        if func is not None:
            return func
    return standard_slots.get(name)

