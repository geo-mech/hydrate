"""
检查Seepage模型可能存在的问题，并返回问题列表.
"""
from typing import List

from zmlx.exts import Seepage


def check_seepage(model: Seepage) -> List[str]:
    """
    假设渗流模型，返回一系列(可能存在的)问题的描述. 后续可能会逐步实现功能，目前尚未完成。
    Args:
        model: Seepage模型
    Returns:
        可能的问题列表
    """
    problems = []

    # 检查模型的单元数量
    if model.cell_number < 2:
        problems.append(
            f"模型的单元数量应该大于等于2，当前为{model.cell_number}"
        )

    # 检查模型的面数量
    if model.face_number < 1:
        problems.append(
            f"模型的面数量应该大于等于1，当前为{model.face_number}"
        )

    # 对于宏观模型，检查重力的设置
    if model.cell_number > 0:
        z0, z1 = model.get_pos_range(2)
        if abs(z0 - z1) > 10.0:
            from zmlx.geometry import point_distance
            if point_distance(model.gravity, [0, 0, -9.8]) > 1.0:
                problems.append(
                    f"对于宏观尺度的模型，重力应该为[-0.0, 0.0, -9.8]，当前为{model.gravity}"
                )

    return problems
