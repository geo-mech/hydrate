import warnings
from ctypes import c_double, c_void_p, c_size_t, c_bool, c_char_p, CFUNCTYPE
from typing import Optional, Iterable, Tuple, List, Union

from zmlx.exts._ary import Array3
from zmlx.exts._coord import Coord3
from zmlx.exts._dll import core, make_c_char_p
from zmlx.exts._str import String
from zmlx.exts._utils import (
    HasCells, HasHandle, Iterator, Object, attr_in_range, get_distance, get_index, IDX_INF, log, make_parent,
    check_ipath
)
from zmlx.exts._vec import UintVector, Vector, IntVector


class Mesh3(HasHandle):
    """
    三维网格类，由点（Node）、线（Link）、面（Face）、体（Body）所组成的网络。
    """

    class Node(Object):
        """
        三维网格中的节点类。

        Attributes:
            model (Mesh3): 节点所属的网格模型。
            index (int): 节点的索引。
        """

        def __init__(self, model, index):
            """
            初始化节点对象。

            Args:
                model (Mesh3): 节点所属的网格模型。
                index (int): 节点的索引，必须小于模型的节点数量。
            """
            assert isinstance(model, Mesh3)
            assert index < model.node_number
            self.model = model
            self.index = index

        core.use(c_double, 'mesh3_get_node_pos', c_void_p, c_size_t, c_size_t)

        @property
        def pos(self):
            """
            返回节点的位置。

            Returns:
                list: 包含节点三个坐标的列表。
            """
            return [core.mesh3_get_node_pos(self.model.handle, self.index, i) for i in range(3)]

        core.use(None, 'mesh3_set_node_pos', c_void_p, c_size_t, c_size_t, c_double)

        @pos.setter
        def pos(self, value):
            """
            设置节点的位置。

            Args:
                value (list): 包含三个坐标的列表，用于设置节点的位置。
            """
            assert len(value) == 3
            for i in range(3):
                core.mesh3_set_node_pos(self.model.handle, self.index, i, value[i])

        core.use(c_size_t, 'mesh3_get_node_link_number', c_void_p, c_size_t)

        @property
        def link_number(self) -> int:
            """
            返回与节点相连的线的数量。

            Returns:
                int: 与节点相连的线的数量。
            """
            return core.mesh3_get_node_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_node_face_number', c_void_p, c_size_t)

        @property
        def face_number(self) -> int:
            """
            返回与节点相连的面的数量。

            Returns:
                int: 与节点相连的面的数量。
            """
            return core.mesh3_get_node_face_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_node_body_number', c_void_p, c_size_t)

        @property
        def body_number(self) -> int:
            """
            返回与节点相连的体的数量。

            Returns:
                int: 与节点相连的体的数量。
            """
            return core.mesh3_get_node_body_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_node_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index) -> Optional['Mesh3.Link']:
            """
            根据索引获取与节点相连的线。

            Args:
                index (int): 线的索引。

            Returns:
                Link: 与节点相连的线对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.link_number)
            if index is not None:
                i = core.mesh3_get_node_link_id(self.model.handle, self.index,
                                                index)
                return self.model.get_link(i)
            else:
                return None

        core.use(c_size_t, 'mesh3_get_node_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index) -> Optional['Mesh3.Face']:
            """
            根据索引获取与节点相连的面。

            Args:
                index (int): 面的索引。

            Returns:
                Face: 与节点相连的面对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.face_number)
            if index is not None:
                i = core.mesh3_get_node_face_id(self.model.handle, self.index,
                                                index)
                return self.model.get_face(i)
            else:
                return None

        core.use(c_size_t, 'mesh3_get_node_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index) -> Optional['Mesh3.Body']:
            """
            根据索引获取与节点相连的体。

            Args:
                index (int): 体的索引。

            Returns:
                Body: 与节点相连的体对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.body_number)
            if index is not None:
                i = core.mesh3_get_node_body_id(self.model.handle, self.index,
                                                index)
                return self.model.get_body(i)
            else:
                return None

        @property
        def links(self) -> Iterable['Mesh3.Link']:
            """
            返回与节点相连的所有线的迭代器。

            Returns:
                Iterator: 与节点相连的所有线的迭代器。
            """
            return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

        @property
        def faces(self) -> Iterable['Mesh3.Face']:
            """
            返回与节点相连的所有面的迭代器。

            Returns:
                Iterator: 与节点相连的所有面的迭代器。
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        @property
        def bodies(self) -> Iterable['Mesh3.Body']:
            """
            返回与节点相连的所有体的迭代器。

            Returns:
                Iterator: 与节点相连的所有体的迭代器。
            """
            return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

        core.use(c_double, 'mesh3_get_node_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_node_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取节点的属性值。

            Args:
                index (int): 属性的索引。
                default_val (any): 如果索引无效或属性值不在有效范围内，返回的默认值。
                **valid_range: 属性值的有效范围。

            Returns:
                any: 节点的属性值，如果索引无效或属性值不在有效范围内，则返回默认值。
            """
            if index is None:
                return default_val
            value = core.mesh3_get_node_attr(self.model.handle, self.index,
                                             index)
            if attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置节点的属性值。

            Args:
                index (int): 属性的索引。
                value (any): 属性的值，如果为 None，则设置为 1.0e200。

            Returns:
                Node: 当前节点对象。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_node_attr(self.model.handle, self.index, index, value)
            return self

    class Link(Object):
        """
        三维网格中的线类。

        Attributes:
            model (Mesh3): 线所属的网格模型。
            index (int): 线的索引。
        """

        def __init__(self, model, index):
            """
            初始化线对象。

            Args:
                model (Mesh3): 线所属的网格模型。
                index (int): 线的索引，必须小于模型的线数量。
            """
            assert isinstance(model, Mesh3)
            assert index < model.link_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'mesh3_get_link_node_number', c_void_p, c_size_t)

        @property
        def node_number(self) -> int:
            """
            返回线所连接的节点数量。

            Returns:
                int: 线所连接的节点数量。
            """
            return core.mesh3_get_link_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_link_face_number', c_void_p, c_size_t)

        @property
        def face_number(self) -> int:
            """
            返回与线相连的面的数量。

            Returns:
                int: 与线相连的面的数量。
            """
            return core.mesh3_get_link_face_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_link_body_number', c_void_p, c_size_t)

        @property
        def body_number(self) -> int:
            """
            返回与线相连的体的数量。

            Returns:
                int: 与线相连的体的数量。
            """
            return core.mesh3_get_link_body_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_link_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, index) -> Optional['Mesh3.Node']:
            """
            根据索引获取线所连接的节点。

            Args:
                index (int): 节点的索引。

            Returns:
                Node: 线所连接的节点对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.node_number)
            if index is not None:
                i = core.mesh3_get_link_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)
            else:
                return None

        core.use(c_size_t, 'mesh3_get_link_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index) -> Optional['Mesh3.Face']:
            """
            根据索引获取与线相连的面。

            Args:
                index (int): 面的索引。

            Returns:
                Face: 与线相连的面对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.face_number)
            if index is not None:
                i = core.mesh3_get_link_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)
            else:
                return None

        core.use(c_size_t, 'mesh3_get_link_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index) -> Optional['Mesh3.Body']:
            """
            根据索引获取与线相连的体。

            Args:
                index (int): 体的索引。

            Returns:
                Body: 与线相连的体对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.body_number)
            if index is not None:
                i = core.mesh3_get_link_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)
            else:
                return None

        @property
        def nodes(self) -> Iterable['Mesh3.Node']:
            """
            返回线所连接的所有节点的迭代器。

            Returns:
                Iterator: 线所连接的所有节点的迭代器。
            """
            return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

        @property
        def faces(self) -> Iterable['Mesh3.Face']:
            """
            返回与线相连的所有面的迭代器。

            Returns:
                Iterator: 与线相连的所有面的迭代器。
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        @property
        def bodies(self) -> Iterable['Mesh3.Body']:
            """
            返回与线相连的所有体的迭代器。

            Returns:
                Iterator: 与线相连的所有体的迭代器。
            """
            return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

        @property
        def length(self) -> float:
            """
            返回线的长度。

            Returns:
                float: 线的长度。
            """
            assert self.node_number == 2
            return get_distance(self.get_node(0).pos, self.get_node(1).pos)

        @property
        def pos(self):
            """
            返回线的中心点位置。

            Returns:
                tuple: 包含线中心点三个坐标的元组。
            """
            assert self.node_number == 2
            p0, p1 = self.get_node(0).pos, self.get_node(1).pos
            return tuple([(p0[i] + p1[i]) / 2 for i in range(len(p0))])

        core.use(c_double, 'mesh3_get_link_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_link_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取线的属性值。

            Args:
                index (int): 属性的索引。
                default_val (any): 如果索引无效或属性值不在有效范围内，返回的默认值。
                **valid_range: 属性值的有效范围。

            Returns:
                any: 线的属性值，如果索引无效或属性值不在有效范围内，则返回默认值。
            """
            if index is None:
                return default_val
            value = core.mesh3_get_link_attr(self.model.handle, self.index, index)
            if attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置线的属性值。

            Args:
                index (int): 属性的索引。
                value (any): 属性的值，如果为 None，则设置为 1.0e200。

            Returns:
                Link: 当前线对象。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_link_attr(self.model.handle, self.index, index, value)
            return self

    class Face(Object):
        """
        三维网格中的面类。

        Attributes:
            model (Mesh3): 面所属的网格模型。
            index (int): 面的索引。
        """

        def __init__(self, model, index):
            """
            初始化面对象。

            Args:
                model (Mesh3): 面所属的网格模型。
                index (int): 面的索引，必须小于模型的面数量。
            """
            assert isinstance(model, Mesh3)
            assert index < model.face_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'mesh3_get_face_node_number',
                 c_void_p, c_size_t)

        @property
        def node_number(self) -> int:
            """
            返回面所包含的节点数量。

            Returns:
                int: 面所包含的节点数量。
            """
            return core.mesh3_get_face_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_face_link_number', c_void_p, c_size_t)

        @property
        def link_number(self) -> int:
            """
            返回面所包含的线的数量。

            Returns:
                int: 面所包含的线的数量。
            """
            return core.mesh3_get_face_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_face_body_number', c_void_p, c_size_t)

        @property
        def body_number(self) -> int:
            """
            返回与面相连的体的数量。

            Returns:
                int: 与面相连的体的数量。
            """
            return core.mesh3_get_face_body_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_face_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, index) -> Optional['Mesh3.Node']:
            """
            根据索引获取面所包含的节点。

            Args:
                index (int): 节点的索引。

            Returns:
                Node: 面所包含的节点对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.node_number)
            if index is not None:
                i = core.mesh3_get_face_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)
            else:
                return None

        core.use(c_size_t, 'mesh3_get_face_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index) -> Optional['Mesh3.Link']:
            """
            根据索引获取面所包含的线。

            Args:
                index (int): 线的索引。

            Returns:
                Link: 面所包含的线对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.link_number)
            if index is not None:
                i = core.mesh3_get_face_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)
            else:
                return None

        core.use(c_size_t, 'mesh3_get_face_body_id', c_void_p, c_size_t, c_size_t)

        def get_body(self, index) -> Optional['Mesh3.Body']:
            """
            根据索引获取与面相连的体。

            Args:
                index (int): 体的索引。

            Returns:
                Body: 与面相连的体对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.body_number)
            if index is not None:
                i = core.mesh3_get_face_body_id(self.model.handle, self.index, index)
                return self.model.get_body(i)
            else:
                return None

        @property
        def nodes(self) -> Iterable['Mesh3.Node']:
            """
            返回面所包含的所有节点的迭代器。

            Returns:
                Iterator: 面所包含的所有节点的迭代器。
            """
            return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

        @property
        def links(self) -> Iterable['Mesh3.Link']:
            """
            返回面所包含的所有线的迭代器。

            Returns:
                Iterator: 面所包含的所有线的迭代器。
            """
            return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

        @property
        def bodies(self) -> Iterable['Mesh3.Body']:
            """
            返回与面相连的所有体的迭代器。

            Returns:
                Iterator: 与面相连的所有体的迭代器。
            """
            return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

        core.use(c_double, 'mesh3_get_face_area', c_void_p, c_size_t)

        @property
        def area(self) -> float:
            """
            返回面的面积。

            Returns:
                float: 面的面积。
            """
            return core.mesh3_get_face_area(self.model.handle, self.index)

        @property
        def pos(self):
            """
            返回面的位置（节点的平均位置）。

            Returns:
                tuple: 包含面位置三个坐标的元组。
            """
            x, y, z = 0, 0, 0
            n = 0
            for node in self.nodes:
                xi, yi, zi = node.pos
                x += xi
                y += yi
                z += zi
                n += 1
            if n > 0:
                return x / n, y / n, z / n
            else:
                return None

        core.use(c_double, 'mesh3_get_face_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_face_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取面的属性值。

            Args:
                index (int): 属性的索引。
                default_val (any): 如果索引无效或属性值不在有效范围内，返回的默认值。
                **valid_range: 属性值的有效范围。

            Returns:
                any: 面的属性值，如果索引无效或属性值不在有效范围内，则返回默认值。
            """
            if index is None:
                return default_val
            value = core.mesh3_get_face_attr(self.model.handle, self.index, index)
            if attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置面的属性值。

            Args:
                index (int): 属性的索引。
                value (any): 属性的值，如果为 None，则设置为 1.0e200。

            Returns:
                Face: 当前面对象。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_face_attr(self.model.handle, self.index, index, value)
            return self

    class Body(Object):
        """
        三维网格中的体类。

        Attributes:
            model (Mesh3): 体所属的网格模型。
            index (int): 体的索引。
        """

        def __init__(self, model, index):
            """
            初始化体对象。

            Args:
                model (Mesh3): 体所属的网格模型。
                index (int): 体的索引，必须小于模型的体数量。
            """
            assert isinstance(model, Mesh3)
            assert index < model.body_number
            self.model = model
            self.index = index

        core.use(c_size_t, 'mesh3_get_body_node_number', c_void_p, c_size_t)

        @property
        def node_number(self) -> int:
            """
            返回体所包含的节点数量。

            Returns:
                int: 体所包含的节点数量。
            """
            return core.mesh3_get_body_node_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_body_link_number', c_void_p, c_size_t)

        @property
        def link_number(self) -> int:
            """
            返回体所包含的线的数量。

            Returns:
                int: 体所包含的线的数量。
            """
            return core.mesh3_get_body_link_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_body_face_number', c_void_p, c_size_t)

        @property
        def face_number(self) -> int:
            """
            返回体所包含的面的数量。

            Returns:
                int: 体所包含的面的数量。
            """
            return core.mesh3_get_body_face_number(self.model.handle, self.index)

        core.use(c_size_t, 'mesh3_get_body_node_id', c_void_p, c_size_t, c_size_t)

        def get_node(self, index) -> Optional['Mesh3.Node']:
            """
            根据索引获取体所包含的节点。

            Args:
                index (int): 节点的索引。

            Returns:
                Node: 体所包含的节点对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.node_number)
            if index is not None:
                i = core.mesh3_get_body_node_id(self.model.handle, self.index, index)
                return self.model.get_node(i)
            else:
                return None

        core.use(c_size_t, 'mesh3_get_body_link_id', c_void_p, c_size_t, c_size_t)

        def get_link(self, index) -> Optional['Mesh3.Link']:
            """
            根据索引获取体所包含的线。

            Args:
                index (int): 线的索引。

            Returns:
                Link: 体所包含的线对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.link_number)
            if index is not None:
                i = core.mesh3_get_body_link_id(self.model.handle, self.index, index)
                return self.model.get_link(i)
            else:
                return None

        core.use(c_size_t, 'mesh3_get_body_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index) -> Optional['Mesh3.Face']:
            """
            根据索引获取体所包含的面。

            Args:
                index (int): 面的索引。

            Returns:
                Face: 体所包含的面对象，如果索引无效则返回 None。
            """
            index = get_index(index, self.face_number)
            if index is not None:
                i = core.mesh3_get_body_face_id(self.model.handle, self.index, index)
                return self.model.get_face(i)
            else:
                return None

        @property
        def nodes(self) -> Iterable['Mesh3.Node']:
            """
            返回体所包含的所有节点的迭代器。

            Returns:
                Iterator: 体所包含的所有节点的迭代器。
            """
            return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

        @property
        def links(self) -> Iterable['Mesh3.Link']:
            """
            返回体所包含的所有线的迭代器。

            Returns:
                Iterator: 体所包含的所有线的迭代器。
            """
            return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

        @property
        def faces(self) -> Iterable['Mesh3.Face']:
            """
            返回体所包含的所有面的迭代器。

            Returns:
                Iterator: 体所包含的所有面的迭代器。
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

        @property
        def pos(self):
            """
            返回体的位置（节点的平均位置）。

            Returns:
                tuple: 包含体位置三个坐标的元组。
            """
            x, y, z = 0, 0, 0
            n = 0
            for node in self.nodes:
                xi, yi, zi = node.pos
                x += xi
                y += yi
                z += zi
                n += 1
            if n > 0:
                return x / n, y / n, z / n
            else:
                return None

        core.use(c_double, 'mesh3_get_body_volume', c_void_p, c_size_t)

        @property
        def volume(self):
            """
            返回体的体积。

            Returns:
                float: 体的体积。
            """
            return core.mesh3_get_body_volume(self.model.handle, self.index)

        core.use(c_double, 'mesh3_get_body_attr', c_void_p, c_size_t, c_size_t)
        core.use(None, 'mesh3_set_body_attr', c_void_p, c_size_t, c_size_t, c_double)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取体的属性值。

            Args:
                index (int): 属性的索引。
                default_val (any): 如果索引无效或属性值不在有效范围内，返回的默认值。
                **valid_range: 属性值的有效范围。

            Returns:
                any: 体的属性值，如果索引无效或属性值不在有效范围内，则返回默认值。
            """
            if index is None:
                return default_val
            value = core.mesh3_get_body_attr(self.model.handle, self.index, index)
            if attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        def set_attr(self, index, value):
            """
            设置体的属性值。

            Args:
                index (int): 属性的索引。
                value (any): 属性的值，如果为 None，则设置为 1.0e200。

            Returns:
                Body: 当前体对象。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.mesh3_set_body_attr(self.model.handle, self.index, index, value)
            return self

        core.use(c_bool, 'mesh3_body_contains', c_void_p, c_size_t, c_double, c_double, c_double)

        def contains(self, pos):
            """
            判断给定的位置是否包含在体中。

            Args:
                pos (list): 包含三个坐标的列表，表示要判断的位置。

            Returns:
                bool: 如果位置包含在体中返回 True，否则返回 False。
            """
            assert len(pos) == 3, f'pos = {pos}'
            return core.mesh3_body_contains(self.model.handle, self.index, *pos)

    core.use(c_void_p, 'new_mesh3')
    core.use(None, 'del_mesh3', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化 Mesh3 对象。

        Args:
            path (str, optional): 要加载的网格文件的路径。
            handle (any, optional): 网格的句柄。
        """
        super().__init__(handle, core.new_mesh3, core.del_mesh3)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
        try:
            name = type(self).__name__
            log(f'{name} created', tag=f'{name}_Init')
        except:
            pass

    def __repr__(self):
        return (
            f'{type(self).__name__}(handle={int(self.handle)}, '
            f'node_n={self.node_number}, link_n={self.link_number}, '
            f'face_n={self.face_number}, body_n={self.body_number})')

    core.use(None, 'mesh3_save', c_void_p, c_char_p)

    def save(self, path: str):
        """
        序列化保存网格数据。

        Args:
            path (str): 保存文件的路径。

        可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）
        """
        if isinstance(path, str):
            make_parent(path)
            core.mesh3_save(self.handle, make_c_char_p(path))

    core.use(None, 'mesh3_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        读取序列化的网格文件。

        Args:
            path (str): 要读取的文件路径。

        根据扩展名确定文件格式（txt、xml 和二进制），请参考 save 函数。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.mesh3_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'mesh3_get_node_number', c_void_p)

    @property
    def node_number(self) -> int:
        """
        返回网格中的节点数量。

        Returns:
            int: 网格中的节点数量。
        """
        return core.mesh3_get_node_number(self.handle)

    core.use(c_size_t, 'mesh3_get_link_number', c_void_p)

    @property
    def link_number(self) -> int:
        """
        返回网格中的线的数量。

        Returns:
            int: 网格中的线的数量。
        """
        return core.mesh3_get_link_number(self.handle)

    core.use(c_size_t, 'mesh3_get_face_number', c_void_p)

    @property
    def face_number(self) -> int:
        """
        返回网格中的面的数量。

        Returns:
            int: 网格中的面的数量。
        """
        return core.mesh3_get_face_number(self.handle)

    core.use(c_size_t, 'mesh3_get_body_number', c_void_p)

    @property
    def body_number(self) -> int:
        """
        返回网格中的体的数量。

        Returns:
            int: 网格中的体的数量。
        """
        return core.mesh3_get_body_number(self.handle)

    def get_node(self, index) -> Optional['Mesh3.Node']:
        """
        根据索引获取网格中的节点。

        Args:
            index (int): 节点的索引。

        Returns:
            Node: 网格中的节点对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.node_number)
        if index is not None:
            return Mesh3.Node(self, index)
        else:
            return None

    def get_link(self, index) -> Optional['Mesh3.Link']:
        """
        根据索引获取网格中的线。

        Args:
            index (int): 线的索引。

        Returns:
            Link: 网格中的线对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.link_number)
        if index is not None:
            return Mesh3.Link(self, index)
        else:
            return None

    def get_face(self, index) -> Optional['Mesh3.Face']:
        """
        根据索引获取网格中的面。

        Args:
            index (int): 面的索引。

        Returns:
            Face: 网格中的面对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.face_number)
        if index is not None:
            return Mesh3.Face(self, index)
        else:
            return None

    def get_body(self, index) -> Optional['Mesh3.Body']:
        """
        根据索引获取网格中的体。

        Args:
            index (int): 体的索引。

        Returns:
            Body: 网格中的体对象，如果索引无效则返回 None。
        """
        index = get_index(index, self.body_number)
        if index is not None:
            return Mesh3.Body(self, index)
        else:
            return None

    @property
    def nodes(self) -> Iterable['Mesh3.Node']:
        """
        返回网格中所有节点的迭代器。

        Returns:
            Iterator: 网格中所有节点的迭代器。
        """
        return Iterator(self, self.node_number, lambda m, ind: m.get_node(ind))

    @property
    def links(self) -> Iterable['Mesh3.Link']:
        """
        返回网格中所有线的迭代器。

        Returns:
            Iterator: 网格中所有线的迭代器。
        """
        return Iterator(self, self.link_number, lambda m, ind: m.get_link(ind))

    @property
    def faces(self) -> Iterable['Mesh3.Face']:
        """
        返回网格中所有面的迭代器。

        Returns:
            Iterator: 网格中所有面的迭代器。
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    @property
    def bodies(self) -> Iterable['Mesh3.Body']:
        """
        返回网格中所有体的迭代器。

        Returns:
            Iterator: 网格中所有体的迭代器。
        """
        return Iterator(self, self.body_number, lambda m, ind: m.get_body(ind))

    core.use(c_size_t, 'mesh3_add_node', c_void_p, c_double, c_double, c_double)

    def add_node(self, x: float, y: float, z: float) -> Optional['Mesh3.Node']:
        """
        在网格中添加一个节点。

        Args:
            x: 节点的 x 坐标。
            y: 节点的 y 坐标。
            z: 节点的 z 坐标。

        Returns:
            Node: 新添加的节点对象。
        """
        index = core.mesh3_add_node(self.handle, x, y, z)
        return self.get_node(index)

    core.use(c_size_t, 'mesh3_add_link', c_void_p, c_size_t, c_size_t)

    def add_link(self, nodes) -> Optional['Mesh3.Link']:
        """
        在网格中添加一条线。

        Args:
            nodes (list): 包含两个 Node 对象的列表，表示线的两个端点。

        注意，如果添加的线已经存在，则直接返回已有的线。

        Returns:
            Link: 新添加的线对象。
        """
        assert len(nodes) == 2, f'The count of nodes must be 2, but got {len(nodes)}'
        node_ids = [node.index if isinstance(node, Mesh3.Node) else node for node in nodes]
        index = core.mesh3_add_link(
            self.handle, node_ids[0], node_ids[1])
        return self.get_link(index)

    core.use(c_size_t, 'mesh3_add_face3', c_void_p, c_size_t, c_size_t, c_size_t)
    core.use(c_size_t, 'mesh3_add_face4', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)

    def add_face(self, links) -> Optional['Mesh3.Face']:
        """
        根据给定的线创建一个面并返回。

        Args:
            links (list): 包含线对象的列表，用于创建面。

        注意，在创建的过程中，会自动识别线的端点的位置，并且对节点进行排序，
        从而尽可能保证，面的所有的节点，恰好能够按照顺序形成一个闭环。

        Returns:
            Face: 新创建的面对象。
        """
        link_ids = [link.index if isinstance(link, Mesh3.Link) else link for link in links]
        if len(link_ids) == 3:
            index = core.mesh3_add_face3(
                self.handle, link_ids[0],
                link_ids[1], link_ids[2])
            return self.get_face(index)
        elif len(link_ids) == 4:
            index = core.mesh3_add_face4(
                self.handle, link_ids[0],
                link_ids[1], link_ids[2], link_ids[3])
            return self.get_face(index)
        else:
            return None

    core.use(c_size_t, 'mesh3_add_body4', c_void_p, c_size_t, c_size_t, c_size_t, c_size_t)
    core.use(c_size_t, 'mesh3_add_body6', c_void_p, c_size_t, c_size_t,
             c_size_t, c_size_t, c_size_t, c_size_t)

    def add_body(self, faces) -> Optional['Mesh3.Body']:
        """
        根据给定的面创建一个体并返回。

        Args:
            faces (list): 包含面对象的列表，用于创建体。

        Returns:
            Body: 新创建的体对象。
        """
        face_ids = [face.index if isinstance(face, Mesh3.Face) else face
                    for face in faces]
        if len(face_ids) == 4:
            index = core.mesh3_add_body4(
                self.handle, face_ids[0],
                face_ids[1], face_ids[2],
                face_ids[3])
            return self.get_body(index)
        elif len(face_ids) == 6:
            index = core.mesh3_add_body6(
                self.handle, face_ids[0],
                face_ids[1], face_ids[2],
                face_ids[3],
                face_ids[4], face_ids[5])
            return self.get_body(index)
        else:
            return None

    core.use(None, 'mesh3_change_view', c_void_p, c_void_p, c_void_p)

    def change_view(self, c_new, c_old) -> 'Mesh3':
        """
        改变网格的视图。

        Args:
            c_new (Coord3): 新的坐标系统。
            c_old (Coord3): 旧的坐标系统。

        Returns:
            Mesh3: 当前网格对象。
        """
        assert isinstance(c_new, Coord3)
        assert isinstance(c_old, Coord3)
        core.mesh3_change_view(self.handle, c_new.handle, c_old.handle)
        return self

    core.use(None, 'mesh3_get_slice', c_void_p, c_void_p, c_void_p)

    def get_slice(self, node_kept) -> 'Mesh3':
        """
        获取网格的切片。

        Args:
            node_kept (function): 一个函数，用于判断节点是否保留。

        Returns:
            Mesh3: 切片后的网格对象。
        """
        kernel = CFUNCTYPE(c_bool, c_double, c_double, c_double)
        data = Mesh3()
        core.mesh3_get_slice(data.handle, self.handle, kernel(node_kept))
        return data

    core.use(None, 'mesh3_append', c_void_p, c_void_p)

    def append(self, other) -> 'Mesh3':
        """
        将另一个网格对象追加到当前网格对象中。

        Args:
            other (Mesh3): 要追加的网格对象。

        Returns:
            Mesh3: 当前网格对象。
        """
        assert isinstance(other, Mesh3)
        core.mesh3_append(self.handle, other.handle)
        return self

    core.use(None, 'mesh3_del_nodes', c_void_p, c_void_p)
    core.use(None, 'mesh3_del_isolated_nodes', c_void_p)

    def del_nodes(self, should_del=None):
        """
        删除网格中的节点。

        Args:
            should_del (function, optional): 一个函数，用于判断节点是否应该删除。如果为 None，则删除所有孤立节点。
        """
        if should_del is None:
            core.mesh3_del_isolated_nodes(self.handle)
        else:
            kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_nodes(self.handle, kernel(should_del))

    core.use(None, 'mesh3_del_links', c_void_p, c_void_p)
    core.use(None, 'mesh3_del_isolated_links', c_void_p)

    def del_links(self, should_del=None):
        """
        删除网格中的线。

        Args:
            should_del (function, optional): 一个函数，用于判断线是否应该删除。
                如果为 None，则删除所有孤立线。
        """
        if should_del is None:
            core.mesh3_del_isolated_links(self.handle)
        else:
            kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_links(self.handle, kernel(should_del))

    core.use(None, 'mesh3_del_faces', c_void_p, c_void_p)
    core.use(None, 'mesh3_del_isolated_faces', c_void_p)

    def del_faces(self, should_del=None):
        """
        删除网格中的面。

        Args:
            should_del (function, optional): 一个函数，用于判断面是否应该删除。
                如果为 None，则删除所有孤立面。
        """
        if should_del is None:
            core.mesh3_del_isolated_faces(self.handle)
        else:
            kernel = CFUNCTYPE(c_bool, c_size_t)
            core.mesh3_del_faces(self.handle, kernel(should_del))

    core.use(None, 'mesh3_del_bodies', c_void_p, c_void_p)

    def del_bodies(self, should_del=None):
        """
        删除网格中的体。

        Args:
            should_del (function): 一个函数，用于判断体是否应该删除。
        """
        assert should_del is not None
        kernel = CFUNCTYPE(c_bool, c_size_t)
        core.mesh3_del_bodies(self.handle, kernel(should_del))

    def del_isolated_nodes(self):
        """
        删除网格中的孤立节点。
        """
        core.mesh3_del_isolated_nodes(self.handle)

    def del_isolated_links(self):
        """
        删除网格中的孤立线。
        """
        core.mesh3_del_isolated_links(self.handle)

    def del_isolated_faces(self):
        """
        删除网格中的孤立面。
        """
        core.mesh3_del_isolated_faces(self.handle)

    core.use(None, 'mesh3_print_trimesh',
             c_void_p, c_char_p, c_char_p,
             c_size_t, c_size_t, c_size_t)

    @staticmethod
    def print_trimesh(vertex_file, triangle_file, data, index_start_from=1,
                      na=IDX_INF, fa=IDX_INF):
        """
        将三角形网格信息打印到文件。

        Args:
            vertex_file (str): 顶点文件的路径。
            triangle_file (str): 三角形文件的路径。
            data (Mesh3): 要打印的网格对象。
            index_start_from (int, optional): 索引的起始值，默认为 1。
            na (int, optional): 无效节点的索引值，默认为 IDX_INF。
            fa (int, optional): 无效面的索引值，默认为 IDX_INF。

        注意，给定的文件路径绝对不能包含中文字符，否则会出错。
        """
        assert isinstance(data, Mesh3)
        core.mesh3_print_trimesh(
            data.handle, make_c_char_p(vertex_file),
            make_c_char_p(triangle_file),
            index_start_from, na, fa)

    core.use(None, 'mesh3_create_tri',
             c_void_p, c_double, c_double,
             c_double, c_double, c_double)

    @staticmethod
    def create_tri(x1, y1, x2, y2, edge_length):
        """
        在x-y平面创建等边三角形网格。

        Args:
            x1 (float): 矩形区域x轴起始坐标
            y1 (float): 矩形区域y轴起始坐标
            x2 (float): 矩形区域x轴结束坐标
            y2 (float): 矩形区域y轴结束坐标
            edge_length (float): 目标三角形边长（实际边长可能略有不同）

        Returns:
            Mesh3: 生成的二维三角形网格对象

        Note:
            - 生成的网格严格位于z=0平面
            - 实际网格范围可能与指定区域略有差异
            - 三角形排列可能产生锯齿状边界
        """
        data = Mesh3()
        core.mesh3_create_tri(data.handle, x1, y1, x2, y2, edge_length)
        return data

    core.use(None, 'mesh3_create_tetra',
             c_void_p, c_double, c_double, c_double,
             c_double, c_double, c_double, c_double)

    @staticmethod
    def create_tetra(x1, y1, z1, x2, y2, z2, edge_length) -> 'Mesh3':
        """
        在三维区域生成四面体网格。

        Args:
            x1 (float): 立方体区域x轴起始坐标
            y1 (float): 立方体区域y轴起始坐标
            z1 (float): 立方体区域z轴起始坐标
            x2 (float): 立方体区域x轴结束坐标
            y2 (float): 立方体区域y轴结束坐标
            z2 (float): 立方体区域z轴结束坐标
            edge_length (float): 目标四面体边长

        Returns:
            Mesh3: 生成的三维四面体网格对象
        """
        data = Mesh3()
        core.mesh3_create_tetra(data.handle, x1, y1, z1, x2, y2, z2,
                                edge_length)
        return data

    core.use(None, 'mesh3_create_cubic',
             c_void_p,
             c_double, c_double, c_double,
             c_double, c_double, c_double,
             c_double, c_double, c_double)

    core.use(None, 'mesh3_create_cubic_by_lattice3',
             c_void_p, c_void_p)

    @staticmethod
    def create_cube(x1=None, y1=None, z1=None, x2=None, y2=None, z2=None,
                    dx=None,
                    dy=None, dz=None, lat=None, buffer=None) -> 'Mesh3':
        """
        创建立方体结构网格。

        Args:
            x1 (float): 区域x轴最小坐标
            y1 (float): 区域y轴最小坐标
            z1 (float): 区域z轴最小坐标
            x2 (float): 区域x轴最大坐标
            y2 (float): 区域y轴最大坐标
            z2 (float): 区域z轴最大坐标
            dx (float): x方向网格尺寸
            dy (float): y方向网格尺寸（默认同dx）
            dz (float): z方向网格尺寸（默认同dx）
            lat (Lattice3): 晶格结构对象
            buffer (Mesh3): 用于存储结果的网格对象

        Returns:
            Mesh3: 生成的立方体网格对象

        Raises:
            AssertionError: 当必需参数未提供时抛出
        """
        if lat is not None:
            if not isinstance(buffer, Mesh3):
                buffer = Mesh3()
            core.mesh3_create_cubic_by_lattice3(buffer.handle, lat.handle)
            return buffer
        else:
            assert x1 is not None and y1 is not None and z1 is not None
            assert x2 is not None and y2 is not None and z2 is not None
            assert dx is not None
            if dy is None:
                dy = dx
            if dz is None:
                dz = dx
            if not isinstance(buffer, Mesh3):
                buffer = Mesh3()
            core.mesh3_create_cubic(buffer.handle, x1, y1, z1, x2, y2, z2, dx,
                                    dy, dz)
            return buffer

    core.use(c_size_t, 'mesh3_get_nearest_node_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_node(self, pos) -> Optional['Mesh3.Node']:
        """
        获取距离给定位置最近的节点。

        Args:
            pos (list/tuple): 三维坐标(x, y, z)

        Returns:
            Mesh3.Node/None: 最近节点对象，若无节点返回None
        """
        if self.node_number > 0:
            pos = [1.0e210 if pos[i] is None else pos[i] for i in range(3)]
            index = core.mesh3_get_nearest_node_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_node(index)
        else:
            return None

    core.use(c_size_t, 'mesh3_get_nearest_link_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_link(self, pos) -> Optional['Mesh3.Link']:
        """
        获取距离给定位置最近的线。

        Args:
            pos (list/tuple): 三维坐标(x, y, z)

        Returns:
            Link/None: 最近线对象，无线时返回None
        """
        if self.link_number > 0:
            pos = [1.0e210 if pos[i] is None else pos[i] for i in range(3)]
            index = core.mesh3_get_nearest_link_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_link(index)
        else:
            return None

    core.use(c_size_t, 'mesh3_get_nearest_face_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_face(self, pos) -> Optional['Mesh3.Face']:
        """
        获取距离给定位置最近的面。

        Args:
            pos (list/tuple): 三维坐标(x, y, z)

        Returns:
            Face/None: 最近面对象，无面时返回None
        """
        if self.face_number > 0:
            pos = [1.0e210 if pos[i] is None else pos[i] for i in range(3)]
            index = core.mesh3_get_nearest_face_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_face(index)
        else:
            return None

    core.use(c_size_t, 'mesh3_get_nearest_body_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_body(self, pos) -> Optional['Mesh3.Body']:
        """
        获取距离给定位置最近的体。

        Args:
            pos (list/tuple): 三维坐标(x, y, z)

        Returns:
            Body/None: 最近体对象，无体时返回None
        """
        if self.body_number > 0:
            pos = [1.0e210 if pos[i] is None else pos[i] for i in range(3)]
            index = core.mesh3_get_nearest_body_id(self.handle, pos[0], pos[1], pos[2])
            return self.get_body(index)
        else:
            return None

    core.use(None, 'mesh3_get_loc_range',
             c_void_p, c_void_p, c_void_p)

    def get_pos_range(self, lr=None, rr=None) -> Tuple[List[float], List[float]]:
        """
        获取所有节点的空间坐标范围。

        Args:
            lr (Array3, optional): 用于存储最小坐标的Array3对象，默认创建新实例
            rr (Array3, optional): 用于存储最大坐标的Array3对象，默认创建新实例

        Returns:
            tuple: 包含最小坐标和最大坐标的元组，格式为(lr_list, rr_list)

        Note:
            - 返回的坐标范围按[x_min, y_min, z_min]和[x_max, y_max, z_max]格式
            - 输入参数lr和rr将被直接修改
        """
        if not isinstance(lr, Array3):
            lr = Array3()
        if not isinstance(rr, Array3):
            rr = Array3()
        core.mesh3_get_loc_range(self.handle, lr.handle, rr.handle)
        return lr.to_list(), rr.to_list()


class SeepageMesh(HasHandle, HasCells):
    """
    定义流体计算的网格系统。

    Note:
        由单元格(Cell)和面(Face)组成的网络结构：
        - 每个Cell包含位置和体积属性
        - 每个Face包含面积和长度属性
    """

    class Cell(Object):
        """
        定义网格中的控制体积单元。
        """

        def __init__(self, model: "SeepageMesh", index: int):
            """初始化单元格对象。

            Args:
                model (SeepageMesh): 所属的渗流网格模型
                index (int): 单元格索引，必须满足 0 <= index < model.cell_number

            Raises:
                AssertionError: 如果传入非法类型的参数或索引越界
            """
            assert isinstance(model, SeepageMesh)
            assert isinstance(index, int)
            assert index < model.cell_number
            self.model: SeepageMesh = model
            self.index: int = index

        def __str__(self) -> str:
            """生成单元格的字符串表示。

            Returns:
                str: 包含单元格句柄、索引、位置和体积信息的字符串
            """
            return (
                f'zml.SeepageMesh.Cell(handle = {self.model.handle}, '
                f'index = {self.index}, '
                f'pos = {self.pos}, volume={self.vol})')

        core.use(c_double, 'seepage_mesh_get_cell_pos', c_void_p, c_size_t, c_size_t)
        core.use(None, 'seepage_mesh_set_cell_pos', c_void_p, c_size_t, c_size_t, c_double)

        @property
        def pos(self) -> List[float]:
            """获取/设置单元格中心点坐标。

            Returns:
                List[float]: 三维坐标列表 [x, y, z]，单位：米

            Note:
                设置新坐标时会自动更新关联的Face属性，可能影响计算精度
            """
            return [core.seepage_mesh_get_cell_pos(self.model.handle, self.index, i) for i in range(3)]

        @pos.setter
        def pos(self, value: Union[List[float], Tuple[float, float, float]]):
            """设置单元格中心点坐标。

            Args:
                value (list[float]): 三维坐标列表，长度必须为3

            Raises:
                AssertionError: 如果输入坐标维度不等于3
            """
            assert len(value) == 3
            for dim in range(3):
                core.seepage_mesh_set_cell_pos(self.model.handle, self.index, dim, value[dim])

        def distance(self, other) -> float:
            """计算到另一单元格或坐标点的欧氏距离。

            Args:
                other: 目标单元格或三维坐标

            Returns:
                float: 三维空间中的直线距离，单位：米
            """
            p0 = self.pos
            if hasattr(other, 'pos'):
                p1 = other.pos
            else:
                p1 = other
            return ((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2 + (p0[2] - p1[2]) ** 2) ** 0.5

        core.use(None, 'seepage_mesh_set_cell_volume', c_void_p, c_size_t, c_double)
        core.use(c_double, 'seepage_mesh_get_cell_volume', c_void_p, c_size_t)

        @property
        def vol(self) -> float:
            """获取/设置单元格体积

            Returns:
                float: 单元格体积，单位：立方米

            Note:
                修改体积值会影响质量守恒计算，建议通过网格生成工具统一设置
            """
            return core.seepage_mesh_get_cell_volume(self.model.handle, self.index)

        @vol.setter
        def vol(self, value: float):
            """设置单元格体积

            Args:
                value (float): 新的体积值，必须大于等于0

            Raises:
                ValueError: 如果输入负值
            """
            core.seepage_mesh_set_cell_volume(self.model.handle, self.index, value)

        core.use(c_double, 'seepage_mesh_get_cell_attr', c_void_p, c_size_t, c_size_t)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取单元格自定义属性值。

            Args:
                index (int): 属性索引
                default_val (Any): 当属性无效时的默认值
                **valid_range: 有效值范围约束（如min=0, max=100）

            Returns:
                float: 属性值或默认值
            """
            if index is None:
                return default_val
            value = core.seepage_mesh_get_cell_attr(self.model.handle, self.index, index)
            if attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        core.use(None, 'seepage_mesh_set_cell_attr', c_void_p, c_size_t, c_size_t, c_double)

        def set_attr(self, index, value):
            """
            设置单元格的自定义属性。

            Args:
                index (int): 属性索引，如果为 None 则不进行任何操作。
                value (float): 属性值，如果为 None 则默认设置为 1.0e200。

            Returns:
                Cell: 当前 Cell 对象，方便链式调用。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.seepage_mesh_set_cell_attr(self.model.handle, self.index, index, value)
            return self

        core.use(c_size_t, 'seepage_mesh_cell_get_face_n', c_void_p, c_size_t)

        @property
        def face_number(self):
            """
            获取周边 Face 的数量。

            Returns:
                int: 周边 Face 的数量。
            """
            return core.seepage_mesh_cell_get_face_n(self.model.handle, self.index)

        @property
        def cell_number(self):
            """
            获取周边 Cell 的数量。

            Returns:
                int: 周边 Cell 的数量，与周边 Face 的数量相同。
            """
            return self.face_number

        core.use(c_size_t, 'seepage_mesh_cell_get_face_id', c_void_p, c_size_t, c_size_t)

        def get_face(self, index: int) -> Optional["SeepageMesh.Face"]:
            """
            获取相邻的指定索引的 Face 对象。

            Args:
                index (int): 相邻 Face 的索引，范围是 0 <= index < face_number。

            Returns:
                Face: 相邻的 Face 对象。

            Raises:
                IndexError: 如果索引超出有效范围。
            """
            index_ = get_index(index, self.face_number)
            return self.model.get_face(
                core.seepage_mesh_cell_get_face_id(self.model.handle, self.index, index_))

        core.use(c_size_t, 'seepage_mesh_cell_get_cell_id', c_void_p, c_size_t, c_size_t)

        def get_cell(self, index: int) -> Optional["SeepageMesh.Cell"]:
            """
            返回周边第 index 个 Cell。

            Args:
                index (int): 周边 Cell 的索引，范围是 0 <= index < cell_number。

            Returns:
                Cell: 周边第 index 个 Cell 对象。

            Raises:
                IndexError: 如果索引超出有效范围。
            """
            index_ = get_index(index, self.cell_number)
            return self.model.get_cell(
                core.seepage_mesh_cell_get_cell_id(self.model.handle, self.index, index_))

        @property
        def cells(self) -> Iterable['SeepageMesh.Cell']:
            """
            获取所有相邻单元格的迭代器。

            Returns:
                Iterator[Cell]: 相邻单元格迭代器。
            """
            return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

        @property
        def faces(self) -> Iterable['SeepageMesh.Face']:
            """
            获取此 Cell 周围的所有 Face 的迭代器。

            Returns:
                Iterator[Face]: 此 Cell 周围的所有 Face 的迭代器。
            """
            return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    class Face(Object):
        """
        定义单元格之间的连接通道。
        """

        def __init__(self, model: 'SeepageMesh', index: int):
            """
            初始化Face对象。

            Args:
                model (SeepageMesh): SeepageMesh对象，代表所属的渗流网格模型
                index (int): 面的索引，必须小于模型中的面的数量
            """
            assert isinstance(model, SeepageMesh)
            assert isinstance(index, int)
            assert index < model.face_number
            self.model: SeepageMesh = model
            self.index: int = index

        def __str__(self):
            """
            返回Face对象的字符串表示。

            Returns:
                str: 包含Face对象的句柄、索引、面积和长度信息的字符串。
            """
            return (
                f'zml.SeepageMesh.Face(handle = {self.model.handle}, '
                f'index = {self.index}, '
                f'area = {self.area}, length = {self.length}) ')

        core.use(None, 'seepage_mesh_set_face_area', c_void_p, c_size_t, c_double)
        core.use(c_double, 'seepage_mesh_get_face_area', c_void_p, c_size_t)

        @property
        def area(self):
            """
            获取/设置流动横截面积。

            Returns:
                float: 流动横截面积（单位：平方米）。

            Note:
                修改面积会影响关联的流动计算参数。
            """
            return core.seepage_mesh_get_face_area(self.model.handle, self.index)

        @area.setter
        def area(self, value):
            """
            设置流动横截面积。

            Args:
                value (float): 新的流动横截面积（单位：平方米）。
            """
            core.seepage_mesh_set_face_area(self.model.handle, self.index, value)

        core.use(None, 'seepage_mesh_set_face_length',
                 c_void_p, c_size_t, c_double)
        core.use(c_double, 'seepage_mesh_get_face_length', c_void_p, c_size_t)

        @property
        def length(self):
            """
            获取/设置流动的距离。

            Returns:
                float: 流动的距离（单位：米）。

            Note:
                为了更加清晰的表示“流动距离”的概念，可以调用dist属性。
            """
            return core.seepage_mesh_get_face_length(self.model.handle, self.index)

        @length.setter
        def length(self, value):
            """
            设置流动的距离。

            Args:
                value (float): 新的流动距离（单位：米）。

            Note:
                为了更加清晰的表示“流动距离”的概念，可以调用dist属性。
            """
            core.seepage_mesh_set_face_length(self.model.handle, self.index, value)

        @property
        def dist(self):
            """
            获取/设置流动的距离。

            Returns:
                float: 流动的距离（单位：米）。
            """
            return self.length

        @dist.setter
        def dist(self, value):
            """
            设置流动的距离。

            Args:
                value (float): 新的流动距离（单位：米）。
            """
            self.length = value

        @property
        def pos(self) -> Tuple[float, ...]:
            """
            计算面中心点坐标。

            Returns:
                tuple[float, ...]: 两侧单元格坐标的平均值，以元组形式返回。
            """
            c0 = self.get_cell(0)
            assert isinstance(c0, SeepageMesh.Cell)

            c1 = self.get_cell(1)
            assert isinstance(c1, SeepageMesh.Cell)

            p0 = c0.pos
            p1 = c1.pos
            return tuple([(p0[i] + p1[i]) / 2 for i in range(len(p0))])

        core.use(c_size_t, 'seepage_mesh_get_face_end0', c_void_p, c_size_t)

        @property
        def cell_i0(self):
            """
            返回第0个cell的id。

            Returns:
                int: 第0个cell的id。
            """
            return core.seepage_mesh_get_face_end0(self.model.handle, self.index)

        core.use(c_size_t, 'seepage_mesh_get_face_end1', c_void_p, c_size_t)

        @property
        def cell_i1(self):
            """
            返回第1个cell的id。

            Returns:
                int: 第1个cell的id。
            """
            return core.seepage_mesh_get_face_end1(self.model.handle, self.index)

        @property
        def cell_ids(self):
            """
            获取两端Cell的ID。

            Returns:
                tuple[int]: 包含两端Cell的ID的元组。
            """
            return self.cell_i0, self.cell_i1

        @property
        def link(self):
            """
            获取两端Cell的ID。

            Returns:
                tuple[int]: 包含两端Cell的ID的元组。
            """
            return self.cell_ids

        @property
        def cell_number(self):
            """
            返回与此face相连的cell的数量。

            Returns:
                int: 与此face相连的cell的数量，固定为2。
            """
            return 2

        def get_cell(self, i: int) -> Optional["SeepageMesh.Cell"]:
            """
            获取连接的第i个单元格。

            Args:
                i (int): 单元格索引，只能为0或1。

            Returns:
                Cell: 连接的单元格对象。

            Raises:
                IndexError: 当索引超出0 - 1范围时抛出。
            """
            idx = get_index(i, 2)
            if idx is not None:
                if idx > 0:
                    return self.model.get_cell(self.cell_i1)
                else:
                    return self.model.get_cell(self.cell_i0)
            else:
                return None

        def cells(self) -> Tuple["SeepageMesh.Cell", "SeepageMesh.Cell"]:
            """
            遍历两端的Cell。

            Returns:
                tuple[Cell]: 包含两端Cell对象的元组。
            """
            c0 = self.get_cell(0)
            c1 = self.get_cell(1)
            assert isinstance(c0, SeepageMesh.Cell)
            assert isinstance(c1, SeepageMesh.Cell)
            return c0, c1

        core.use(c_double, 'seepage_mesh_get_face_attr', c_void_p, c_size_t, c_size_t)

        def get_attr(self, index, default_val=None, **valid_range):
            """
            获取第index个自定义属性。

            Args:
                index (int): 属性索引。
                default_val (Any): 默认值，当属性值无效或索引为None时返回。
                **valid_range: 属性值的有效范围，以关键字参数形式传入。

            Returns:
                float: 属性值或默认值。
            """
            if index is None:
                return default_val
            value = core.seepage_mesh_get_face_attr(self.model.handle, self.index, index)
            if attr_in_range(value, **valid_range):
                return value
            else:
                return default_val

        core.use(None, 'seepage_mesh_set_face_attr', c_void_p, c_size_t, c_size_t, c_double)

        def set_attr(self, index, value):
            """
            设置第index个自定义属性。

            Args:
                index (int): 属性索引。
                value (float): 属性值，如果为None则默认设置为1.0e200。

            Returns:
                Face: 当前Face对象，方便链式调用。
            """
            if index is None:
                return self
            if value is None:
                value = 1.0e200
            core.seepage_mesh_set_face_attr(self.model.handle, self.index, index, value)
            return self

    core.use(c_void_p, 'new_seepage_mesh')
    core.use(None, 'del_seepage_mesh', c_void_p)

    def __init__(self, path: Optional[str] = None, handle: Optional[c_void_p] = None):
        """
        初始化SeepageMesh对象

        Args:
            path (str, optional): 加载网格的路径。如果提供，则从该路径加载网格。
            handle (Any, optional): 网格的句柄。如果为None，则从path加载网格。

        Notes:
            如果handle为None，则尝试从path加载网格。
        """
        super().__init__(handle, core.new_seepage_mesh, core.del_seepage_mesh)
        if handle is None:
            if isinstance(path, str):
                self.load(path)
        try:
            name = type(self).__name__
            log(f'{name} created', tag=f'{name}_Init')
        except:
            pass

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}(handle={int(self.handle)}, '
            f'cell_n={self.cell_number}, '
            f'face_n={self.face_number})')

    def __str__(self) -> str:
        """
        返回对象的字符串表示

        Returns:
            str: 包含句柄、cell数量、face数量和总体积的字符串表示。
        """
        return (
            f'{type(self).__name__}(handle={int(self.handle)}, '
            f'cell_n={self.cell_number}, '
            f'face_n={self.face_number}, '
            f'volume={self.volume})')

    core.use(None, 'seepage_mesh_save', c_void_p, c_char_p)

    def save(self, path: str):
        """
        保存网格到指定路径

        Args:
            path (str): 保存网格的路径。

        Notes:
            可选扩展名:
            - .txt: TXT格式（跨平台，基本不可读）
            - .xml: XML格式（特定可读性，体积最大，读写最慢，跨平台）
            - 其他: 二进制格式（最快最小，但Windows和Linux下生成的文件不能互相读取）
        """
        if isinstance(path, str):
            make_parent(path)
            core.seepage_mesh_save(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_mesh_load', c_void_p, c_char_p)

    def load(self, path: str):
        """
        从指定路径加载网格

        Args:
            path (str): 加载网格的路径。

        Notes:
            根据扩展名确定文件格式（txt, xml, 二进制），参考save函数。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.seepage_mesh_load(self.handle, make_c_char_p(path))

    core.use(None, 'seepage_mesh_clear', c_void_p)

    def clear(self):
        """
        清除所有的cell和face
        """
        core.seepage_mesh_clear(self.handle)

    core.use(c_size_t, 'seepage_mesh_get_cell_n', c_void_p)

    @property
    def cell_number(self) -> int:
        """
        返回cell的数量

        Returns:
            int: 网格中cell的数量。
        """
        return core.seepage_mesh_get_cell_n(self.handle)

    def get_cell(self, ind) -> Optional["SeepageMesh.Cell"]:
        """
        返回第ind个cell

        Args:
            ind (int): cell的索引。

        Returns:
            SeepageMesh.Cell: 第ind个cell对象，如果索引有效；否则返回None。
        """
        ind = get_index(ind, self.cell_number)
        if ind is not None:
            return SeepageMesh.Cell(self, ind)
        else:
            return None

    core.use(c_size_t, 'seepage_mesh_get_nearest_cell_id', c_void_p, c_double, c_double, c_double)

    def get_nearest_cell(self, pos: Union[Tuple[float, float, float], List[float]]) -> Optional["SeepageMesh.Cell"]:
        """
        返回与给定位置距离最近的cell

        Args:
            pos (tuple | list): 包含三个浮点数的元组，表示三维空间中的位置。

        Returns:
            SeepageMesh.Cell: 与给定位置距离最近的cell对象，
                如果网格中有cell；否则返回None。
        """
        if self.cell_number > 0:
            pos = [1.0e210 if pos[i] is None else pos[i] for i in range(3)]
            return self.get_cell(core.seepage_mesh_get_nearest_cell_id(self.handle, pos[0], pos[1], pos[2]))
        else:
            return None

    core.use(c_size_t, 'seepage_mesh_get_face_n', c_void_p)

    @property
    def face_number(self) -> int:
        """
        返回face的数量

        Returns:
            int: 网格中face的数量。
        """
        return core.seepage_mesh_get_face_n(self.handle)

    core.use(c_size_t, 'seepage_mesh_get_face', c_void_p, c_size_t, c_size_t)

    def get_face(self, ind=None, cell_0=None, cell_1=None) -> Optional["SeepageMesh.Face"]:
        """
        返回第ind个face，或者找到两个cell之间的face

        Args:
            ind (int, optional): 面的索引。如果提供，则返回该索引对应的face。
            cell_0 (SeepageMesh.Cell, optional): 第一个单元格。
                如果ind未提供，则需要提供此参数。
            cell_1 (SeepageMesh.Cell, optional): 第二个单元格。
                如果ind未提供，则需要提供此参数。

        Returns:
            SeepageMesh.Face: 面的对象，如果找到；否则返回None。

        Raises:
            AssertionError: 如果ind和(cell_0, cell_1)的提供不符合要求。
        """
        if ind is not None:
            assert cell_0 is None and cell_1 is None
            ind = get_index(ind, self.face_number)
            if ind is not None:
                return SeepageMesh.Face(self, ind)
            else:
                return None
        else:
            assert cell_0 is not None and cell_1 is not None
            assert isinstance(cell_0, SeepageMesh.Cell)
            assert isinstance(cell_1, SeepageMesh.Cell)
            assert cell_0.model.handle == self.handle
            assert cell_1.model.handle == self.handle
            ind = core.seepage_mesh_get_face(self.handle, cell_0.index,
                                             cell_1.index)
            if ind < self.face_number:
                return SeepageMesh.Face(self, ind)
            else:
                return None

    core.use(c_size_t, 'seepage_mesh_add_cell', c_void_p)

    def add_cell(self, *, pos=None, vol=None) -> "SeepageMesh.Cell":
        """
        添加一个cell，并且返回这个新添加的cell

        Returns:
            SeepageMesh.Cell: 新添加的cell对象。
        """
        cell = self.get_cell(core.seepage_mesh_add_cell(self.handle))
        assert cell is not None, "Failed to add cell"
        if pos is not None:
            cell.pos = pos
        if vol is not None:
            cell.vol = vol
        return cell

    core.use(c_size_t, 'seepage_mesh_add_face', c_void_p, c_size_t, c_size_t)

    def add_face(self, cell_0, cell_1, *, dist=None, area=None) -> "SeepageMesh.Face":
        """
        添加一个face，连接两个给定的cell

        Args:
            cell_0 (int | SeepageMesh.Cell): 第一个单元格。
            cell_1 (int | SeepageMesh.Cell): 第二个单元格。
            dist: 过流距离 (m)
            area: 过流面积 (m^2)

        Returns:
            SeepageMesh.Face: 新添加的面的对象

        Raises:
            AssertionError: 如果提供的cell不属于当前网格
        """
        if isinstance(cell_0, SeepageMesh.Cell):
            assert cell_0.model.handle == self.handle
            cell_0 = cell_0.index

        if isinstance(cell_1, SeepageMesh.Cell):
            assert cell_1.model.handle == self.handle
            cell_1 = cell_1.index

        face_n = self.face_number
        idx = core.seepage_mesh_add_face(self.handle, cell_0, cell_1)
        face = self.get_face(idx)
        assert face is not None, "Failed to add face"

        if self.face_number > face_n:  # a new face
            assert idx == face_n
            if area is not None:
                face.area = area
            if dist is None:
                p0 = face.get_cell(0).pos
                p1 = face.get_cell(1).pos
                dist = get_distance(p0, p1)
                if dist > 1.0e20 or dist < 1.0e-20:
                    dist = None
            if dist is not None:
                face.dist = dist

        return face

    @property
    def cells(self) -> Iterable['SeepageMesh.Cell']:
        """
        用以迭代所有的cell

        Returns:
            Iterator: 用于迭代所有cell的迭代器。
        """
        return Iterator(self, self.cell_number, lambda m, ind: m.get_cell(ind))

    @property
    def faces(self) -> Iterable['SeepageMesh.Face']:
        """
        用以迭代所有的face

        Returns:
            Iterator: 用于迭代所有face的迭代器。
        """
        return Iterator(self, self.face_number, lambda m, ind: m.get_face(ind))

    @property
    def volume(self):
        """
        返回整个模型整体的体积

        Returns:
            float: 整个模型的总体积，通过累加所有cell的体积得到。
        """
        vol = 0
        for cell in self.cells:
            vol += cell.vol
        return vol

    def load_ascii(self, *args, **kwargs):
        """
        加载ASCII格式的网格数据

        Notes:
            此方法将在2025-5-27之后被移除，请使用zmlx.seepage_mesh.ascii中的函数。
        """
        warnings.warn('SeepageMesh.load_ascii will be removed '
                      'after 2025-5-27, '
                      'please use the function in '
                      'zmlx.seepage_mesh.ascii instead',
                      DeprecationWarning, stacklevel=2)
        from zmlx.seepage_mesh.io import load_ascii
        load_ascii(*args, **kwargs, mesh=self)

    def save_ascii(self, *args, **kwargs):
        """
        保存ASCII格式的网格数据

        Notes:
            此方法将在2025-5-27之后被移除，请使用zmlx.seepage_mesh.ascii中的函数。
        """
        warnings.warn('SeepageMesh.save_ascii will be removed '
                      'after 2025-5-27, '
                      'please use the function in '
                      'zmlx.seepage_mesh.ascii instead',
                      DeprecationWarning, stacklevel=2)
        from zmlx.seepage_mesh.io import save_ascii
        save_ascii(*args, **kwargs, mesh=self)

    @staticmethod
    def load_mesh(*args, **kwargs):
        """
        加载网格数据

        Notes:
            此方法将在2025-5-27之后被移除，请使用zmlx.seepage_mesh.load_mesh中的函数。
        """
        warnings.warn('SeepageMesh.load_mesh will be removed '
                      'after 2025-5-27, '
                      'please use the function in '
                      'zmlx.seepage_mesh.load_mesh instead',
                      DeprecationWarning, stacklevel=2)
        from zmlx.seepage_mesh.io import load_mesh as load
        return load(*args, **kwargs)

    @staticmethod
    def create_cube(*args, **kwargs):
        """
        创建一个立方体网格

        Notes:
            此方法将在2025-5-27之后被移除，请使用zmlx.seepage_mesh.cube.create_cube函数。
        """
        warnings.warn(
            'The zml.SeepageMesh.create_cube will be removed '
            'after 2025-5-27. '
            'please use the function create_cube from zmlx instead',
            DeprecationWarning, stacklevel=2)
        from zmlx.seepage_mesh.cube import create_cube as create
        return create(*args, **kwargs)

    @staticmethod
    def create_cylinder(*args, **kwargs):
        """
        创建一个圆柱体网格

        Notes:
            此方法将在2025-5-27之后被移除，
            请使用zmlx.seepage_mesh.cylinder.create_cylinder函数。
        """
        warnings.warn(
            'The zml.SeepageMesh.create_cylinder will be removed'
            ' after 2025-5-27. '
            'please use zmlx.seepage_mesh.cylinder.create_cylinder instead',
            DeprecationWarning, stacklevel=2)
        from zmlx.seepage_mesh.cylinder import create_cylinder as create
        return create(*args, **kwargs)

    core.use(None, 'seepage_mesh_find_inner_face_ids',
             c_void_p, c_void_p, c_void_p)

    def find_inner_face_ids(self, cell_ids: UintVector, buffer=None):
        """
        给定多个Cell，返回这些Cell内部相互连接的Face的序号

        Args:
            cell_ids (UintVector): 单元格的ID列表。
            buffer (UintVector, optional): 缓冲区，用于存储返回的面的ID。
                如果未提供，则创建一个新的UintVector。

        Returns:
            UintVector: 缓冲区，包含了内部相互连接的面的ID。

        Raises:
            AssertionError: 如果cell_ids不是UintVector类型。
        """
        assert isinstance(cell_ids, UintVector)
        if not isinstance(buffer, UintVector):
            buffer = UintVector()
        core.seepage_mesh_find_inner_face_ids(self.handle, buffer.handle,
                                              cell_ids.handle)
        return buffer

    core.use(None, 'seepage_mesh_from_mesh3', c_void_p, c_void_p)

    @staticmethod
    def from_mesh3(mesh3: Mesh3, buffer=None):
        """
        利用一个Mesh3的Body来创建Cell，Face来创建Face

        Args:
            mesh3 (Mesh3): 一个Mesh3对象，用于创建SeepageMesh的单元格和面。
            buffer (SeepageMesh, optional): 一个可选的SeepageMesh对象，
                用于存储转换后的网格。如果未提供，则创建一个新的SeepageMesh对象。

        Returns:
            SeepageMesh: 如果成功，返回创建的或传入的SeepageMesh对象；否则抛出异常。

        Raises:
            AssertionError: 如果mesh3不是Mesh3类的实例，
            或者buffer不是SeepageMesh类的实例（当提供时）。
        """
        assert isinstance(mesh3, Mesh3)
        if not isinstance(buffer, SeepageMesh):
            buffer = SeepageMesh()
        core.seepage_mesh_from_mesh3(buffer.handle, mesh3.handle)
        return buffer


class ElementMap(HasHandle):
    class Element(Object):
        """
        表示ElementMap中的一个元素。

        Attributes:
            model (ElementMap): 元素所属的ElementMap实例。
            index (int): 元素的索引。
        """

        def __init__(self, model, index):
            """
            初始化Element对象。

            Args:
                model (ElementMap): 元素所属的ElementMap实例。
                index (int): 元素的索引。
            """
            self.model = model
            self.index = index

        core.use(c_size_t, 'element_map_related_count',
                 c_void_p, c_size_t)

        @property
        def size(self):
            """
            获取与该元素相关的元素数量。

            Returns:
                int: 与该元素相关的元素数量。
            """
            return core.element_map_related_count(self.model.handle, self.index)

        core.use(c_size_t, 'element_map_related_id',
                 c_void_p, c_size_t,
                 c_size_t)

        core.use(c_double, 'element_map_related_weight',
                 c_void_p, c_size_t,
                 c_size_t)

        def get_iw(self, i):
            """
            获取与该元素相关的第i个元素的索引和权重。

            Args:
                i (int): 相关元素的索引。

            Returns:
                tuple: 包含相关元素的索引和权重的元组，如果索引有效；否则返回None。
            """
            i = get_index(i, self.size)
            if i is not None:
                ind = core.element_map_related_id(
                    self.model.handle, self.index, i)
                w = core.element_map_related_weight(
                    self.model.handle, self.index, i)
                return ind, w
            else:
                return None

    core.use(c_void_p, 'new_element_map')
    core.use(None, 'del_element_map', c_void_p)

    def __init__(self, path=None, handle=None):
        """
        初始化ElementMap对象。

        Args:
            path (str, optional): 加载ElementMap的文件路径。如果提供，则从该路径加载。
            handle (Any, optional): ElementMap的句柄。如果为None，则尝试从path加载。

        Notes:
            如果handle为None且path是有效的字符串，则从path加载ElementMap。
        """
        super().__init__(handle, core.new_element_map,
                         core.del_element_map)
        if handle is None:
            if isinstance(path, str):
                self.load(path)

    def __repr__(self):
        return f'{type(self).__name__}(handle={int(self.handle)}, size={self.size})'

    core.use(None, 'element_map_save',
             c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存ElementMap到指定路径。

        Args:
            path (str): 保存ElementMap的文件路径。

        Notes:
            可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）
        """
        if isinstance(path, str):
            make_parent(path)
            core.element_map_save(self.handle, make_c_char_p(path))

    core.use(None, 'element_map_load',
             c_void_p, c_char_p)

    def load(self, path):
        """
        从指定路径读取序列化的ElementMap文件。

        Args:
            path (str): 加载ElementMap的文件路径。

        Notes:
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.element_map_load(self.handle, make_c_char_p(path))

    core.use(None, 'element_map_to_str',
             c_void_p, c_size_t)

    def to_str(self):
        """
        将ElementMap转换为字符串。

        Returns:
            str: 表示ElementMap的字符串。
        """
        s = String()
        core.element_map_to_str(self.handle, s.handle)
        return s.to_str()

    core.use(None, 'element_map_from_str',
             c_void_p, c_size_t)

    def from_str(self, s):
        """
        从字符串中加载ElementMap。

        Args:
            s (str): 包含ElementMap数据的字符串。
        """
        s2 = String()
        s2.assign(s)
        core.element_map_from_str(self.handle, s2.handle)

    core.use(c_size_t, 'element_map_size', c_void_p)

    @property
    def size(self):
        """
        获取ElementMap的大小。

        Returns:
            int: ElementMap的大小。
        """
        return core.element_map_size(self.handle)

    core.use(None, 'element_map_clear', c_void_p)

    def clear(self):
        """
        清除ElementMap中的所有元素。
        """
        core.element_map_clear(self.handle)

    core.use(None, 'element_map_add',
             c_void_p, c_void_p, c_void_p)

    def add_element(self, vi, vw):
        """
        向ElementMap中添加一个元素。

        Args:
            vi (IntVector or list): 元素的索引向量。
            vw (Vector or list): 元素的权重向量。

        Notes:
            如果vi和vw不是IntVector和Vector类型，将尝试转换为相应类型。
        """
        if not isinstance(vi, IntVector):
            vi = IntVector(vi)
        if not isinstance(vw, Vector):
            vw = Vector(vw)
        core.element_map_add(self.handle, vi.handle, vw.handle)

    def get_element(self, index):
        """
        获取指定索引的元素。

        Args:
            index (int): 元素的索引。

        Returns:
            ElementMap.Element: 指定索引的元素对象。
        """
        return ElementMap.Element(self, index)

    core.use(None, 'element_map_get',
             c_void_p, c_void_p, c_void_p, c_double)

    def get_values(self, source, buffer=None, default=None):
        """
        根据原始网格中的数据，根据此映射，计算此网格体系内各个网格的数值。

        Args:
            source (Vector): 原始网格中的数据向量。
            buffer (Vector, optional): 用于存储计算结果的缓冲区。
                如果未提供，则创建一个新的Vector。
            default (float, optional): 默认值，用于处理未映射的元素。
                如果未提供，则默认为0.0。

        Returns:
            Vector: 包含计算结果的缓冲区。

        Raises:
            AssertionError: 如果source不是Vector类型。
        """
        assert isinstance(source, Vector)
        if not isinstance(buffer, Vector):
            buffer = Vector()
        if default is None:
            default = 0.0
        core.element_map_get(
            self.handle, buffer.handle, source.handle, default)
        return buffer


class Groups(HasHandle):
    core.use(c_void_p, 'new_groups')
    core.use(None, 'del_groups', c_void_p)

    def __init__(self, handle=None):
        """
        初始化Groups对象。

        Args:
            handle (c_void_p, optional): 指向底层C对象的句柄。如果为None，
                则创建一个新的Groups对象。
        """
        super().__init__(
            handle, core.new_groups, core.del_groups)

    core.use(None, 'groups_save',
             c_void_p, c_char_p)

    def save(self, path):
        """
        序列化保存。可选扩展格式：
            1：.txt
            .TXT 格式
            （跨平台，基本不可读）

            2：.xml
            .XML 格式
            （特定可读性，文件体积最大，读写速度最慢，跨平台）

            3：.其他
            二进制格式
            （最快且最小，但在 Windows 和 Linux 下生成的文件无法互相读取）

        Args:
            path (str): 保存文件的路径。

        Notes:
            如果路径的父目录不存在，会自动创建。
        """
        if isinstance(path, str):
            make_parent(path)
            core.groups_save(self.handle, make_c_char_p(path))

    core.use(None, 'groups_load',
             c_void_p, c_char_p)

    def load(self, path):
        """
        读取序列化文件。
            根据扩展名确定文件格式（txt、xml 和二进制），请参考save函数。

        Args:
            path (str): 加载文件的路径。

        Raises:
            AssertionError: 如果路径无效。
        """
        if isinstance(path, str):
            check_ipath(path, self)
            core.groups_load(self.handle, make_c_char_p(path))

    core.use(c_size_t, 'groups_size', c_void_p)

    @property
    def size(self):
        """
        获取Groups中元素的数量。

        Returns:
            int: Groups中元素的数量。
        """
        return core.groups_size(self.handle)

    core.use(c_void_p, 'groups_get',
             c_void_p, c_size_t)

    def get(self, index):
        """
        获取指定索引的元素。

        Args:
            index (int): 元素的索引。

        Returns:
            UintVector: 包含指定索引元素的UintVector对象。
        """
        handle = core.groups_get(self.handle, index)
        return UintVector(handle=handle)
