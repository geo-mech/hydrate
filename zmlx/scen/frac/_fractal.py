"""
裂缝分形模型
"""
import math
from typing import List, Union, Tuple, Optional


class Branch2:
    """
    二维空间的一个树形分支
    """

    def __init__(self, vertexes: Optional[List[Tuple[float, float]]] = None, width: float = 1.0, rank: int = 0):
        """
        初始化分支
        Args:
            vertexes: 分支的顶点坐标列表，默认值为空列表
            width: 分支的宽度/粗细/权重，默认值为1.0
            rank: 分支的等级，默认值为0，0表示根分支，1表示子分支，以此类推
        """
        self.vertexes: List[Tuple[float, float]] = vertexes if vertexes is not None else []
        self.width: float = width  # 宽度/粗细/权重
        self.rank: int = rank  # 分支的等级
        self.children: List['Branch2'] = []  # 子分支列表

    def add_vertex(self, x, y, l_min=None):
        if l_min is not None:
            dist = math.sqrt((x - self.vertexes[-1][0]) ** 2 + (y - self.vertexes[-1][1]) ** 2)
            if dist < l_min:
                self.vertexes[-1] = (x, y)
            else:
                self.vertexes.append((x, y))
        else:
            self.vertexes.append((x, y))

    @property
    def length(self) -> float:
        res = 0
        for i in range(1, len(self.vertexes)):
            dx = self.vertexes[i][0] - self.vertexes[i - 1][0]
            dy = self.vertexes[i][1] - self.vertexes[i - 1][1]
            res += math.sqrt(dx ** 2 + dy ** 2)
        return res

    @property
    def start(self) -> Tuple[float, float]:
        return self.vertexes[0]

    @property
    def end(self) -> Tuple[float, float]:
        return self.vertexes[-1]

    @property
    def angle(self) -> float:
        dx = self.vertexes[-1][0] - self.vertexes[-2][0]
        dy = self.vertexes[-1][1] - self.vertexes[-2][1]
        return math.atan2(dy, dx)

    @property
    def total_length(self) -> float:
        """
        获取当前分支及其子分支的总长度
        """
        total_length = self.length
        for child in self.children:
            total_length += child.total_length
        return total_length

    @staticmethod
    def create(start: Union[Tuple[float, float], List[float]], angle: float, length: float, width: float = 1.0,
               rank: int = 0) -> 'Branch2':
        """
        根据起始点、角度、长度、宽度和等级创建一个分支
        Args:
            start: 分支的起始点坐标，默认值为(0, 0)
            angle: 分支的角度，默认值为0
            length: 分支的长度，默认值为1.0
            width: 分支的宽度/粗细/权重，默认值为1.0
            rank: 分支的等级，默认值为0，0表示根分支，1表示子分支，以此类推
        Returns:
            创建好的分支对象
        """
        assert len(start) == 2, 'start must be 2D vectors'
        assert length > 0, 'length must be positive'
        vertexes: List[Tuple[float, float]] = [
            (start[0], start[1]),
            (start[0] + length * math.cos(angle), start[1] + length * math.sin(angle)),
        ]
        return Branch2(vertexes=vertexes, width=width, rank=rank)

    @staticmethod
    def create_curve(*, start: Union[Tuple[float, float], List[float]],
                     length: float,
                     angle: float, target_angle: Optional[float], target_angle_weight: float,
                     width: float = 1.0,
                     rank: int = 0, segment_num: int = 1,
                     ) -> 'Branch2':
        """
        创建曲线分支。
        """
        if target_angle is None or target_angle_weight <= 0:
            return Branch2.create(start=start, angle=angle, length=length, width=width, rank=rank)

        assert len(start) == 2, 'start must be 2D vectors'
        assert length > 0, 'length must be positive'

        vertexes: List[Tuple[float, float]] = [
            (start[0], start[1]),
        ]

        if target_angle_weight > 1.0:
            target_angle_weight = 1.0

        assert segment_num > 0, 'segment_num must be positive'
        for i in range(segment_num):
            while angle > target_angle + math.pi:
                angle -= math.pi * 2
            while angle < target_angle - math.pi:
                angle += math.pi * 2
            da = target_angle - angle
            da *= (target_angle_weight / segment_num)
            angle += da
            dx = length * math.cos(angle) / segment_num
            dy = length * math.sin(angle) / segment_num
            vertexes.append((vertexes[-1][0] + dx, vertexes[-1][1] + dy))

        return Branch2(vertexes=vertexes, width=width, rank=rank)


def get_plt_data(branch: Branch2):
    """
    获取当前分支及其子分支的plt数据（用于绘图）
    Returns:
        pos: 一系列线段的坐标，为一个list，list的每一个元素的长度都是4
        w: 一系列线段的宽度，为一个list，长度和pos相同
        c: 一系列线段的颜色，为一个list，长度和pos相同
    """
    pos = [branch.vertexes[0] + branch.vertexes[1]]
    w = [branch.width]
    c = [branch.rank]
    for i in range(2, len(branch.vertexes)):
        pos.append(branch.vertexes[i - 1] + branch.vertexes[i])
        w.append(branch.width)
        c.append(branch.rank)

    for child in branch.children:
        assert isinstance(child, Branch2), 'children must be a Branch2'
        child_pos, child_w, child_c = get_plt_data(child)
        pos.extend(child_pos)
        w.extend(child_w)
        c.extend(child_c)
    return pos, w, c


def show(branch: Branch2, w_min=0.5, w_max=4, cbar=None, xlabel='x/m', ylabel='y/m', aspect='equal',
         caption='裂缝分形',
         **opts):
    """
    显示当前分支及其子分支
    """
    from zmlx.plt import show_fn2
    if cbar is None:
        cbar = dict(label='Rank')
    pos, w, c = get_plt_data(branch)
    show_fn2(pos, w, c, w_min=w_min, w_max=w_max, cbar=cbar, xlabel=xlabel, ylabel=ylabel, aspect=aspect,
             caption=caption, **opts)
