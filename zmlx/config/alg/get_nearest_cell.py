from zmlx.geometry.point_distance import point_distance


def get_nearest_cell(model, pos, mask=None):
    """
    找到model中，距离给定的pos最为接近的cell
    """
    if model.cell_number == 0:
        return

    result = None
    dist = 1.0e100

    # 遍历，找到最接近的cell.
    for cell in model.cells:
        if mask is not None:
            if not mask(cell):  # 只有满足条件的cell才会被检查.
                continue

        # 计算距离
        d = point_distance(cell.pos, pos)
        if result is None or d < dist:
            dist = d
            result = cell  # 更新结果

    # 返回结果
    return result
