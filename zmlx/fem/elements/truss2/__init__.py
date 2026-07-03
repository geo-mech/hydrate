"""
杆单元 Truss Element
特点：只有轴向刚度，只能拉伸 / 压缩，不能承受弯矩、剪力；桁架结构专用（塔吊、屋架、网架）
"""

from zmlx.fem.elements.truss2._stiffness import calc_stiffness
from zmlx.fem.elements.truss2._strain import calc_strain
