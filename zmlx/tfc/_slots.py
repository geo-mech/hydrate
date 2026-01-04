# 一些预定义函数
standard_slots = {'print': print}


def get_slots(slots=None):
    """
    返回包含standard_slots在内的槽函数
    """
    if isinstance(slots, dict):
        return {**standard_slots, **slots}
    else:
        return standard_slots.copy()


def get_slot(name, *, slots=None):
    """
    返回给定名字的slot. 并且，如果给定的slots中不存在，则搜索标准的slots
    """
    if not isinstance(name, str):
        return None

    if slots is not None:
        f = slots.get(name)
        if f is not None:
            return f

    return standard_slots.get(name)
