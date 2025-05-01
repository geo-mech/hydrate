from zml import Mesh3, LinearExpr
from zmlx.geometry.utils import get_center
from zmlx.geometry.utils import point_distance


def create_face_xx(mesh):
    """
    用以计算各个face在x方向上应变的线性表达式.
    """
    assert isinstance(mesh, Mesh3)
    result = []
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        # 分别找到左侧和右侧的两个node
        vl = []
        vr = []
        x_center = face.pos[0]
        for node in face.nodes:
            assert isinstance(node, Mesh3.Node)
            if node.pos[0] > x_center:
                vr.append(node.index)
            else:
                vl.append(node.index)
        assert len(vl) == 2 and len(vr) == 2
        # 两侧的中心距离
        dist = point_distance(get_center(mesh.get_node(vl[0]).pos, mesh.get_node(vl[1]).pos),
                              get_center(mesh.get_node(vr[0]).pos, mesh.get_node(vr[1]).pos))
        # 建立一个表达式
        lex = LinearExpr()
        for node_id in vr:
            x = mesh.get_node(node_id).pos[0]
            lex.add(node_id * 2, 0.5 / dist)
            lex.c -= x * 0.5 / dist
        for node_id in vl:
            x = mesh.get_node(node_id).pos[0]
            lex.add(node_id * 2, -0.5 / dist)
            lex.c += x * 0.5 / dist
        # 完成
        lex.merge()
        result.append(lex)
    # 每一个元素都是一个线性表达式
    return result


def create_face_yy(mesh):
    """
    用以计算各个face在y方向上应变的线性表达式.
    """
    assert isinstance(mesh, Mesh3)
    result = []
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        # 分别找到左侧和右侧的两个node
        vl = []
        vr = []
        y_center = face.pos[1]
        for node in face.nodes:
            assert isinstance(node, Mesh3.Node)
            if node.pos[1] > y_center:
                vr.append(node.index)
            else:
                vl.append(node.index)
        assert len(vl) == 2 and len(vr) == 2
        # 两侧的中心距离
        dist = point_distance(get_center(mesh.get_node(vl[0]).pos, mesh.get_node(vl[1]).pos),
                              get_center(mesh.get_node(vr[0]).pos, mesh.get_node(vr[1]).pos))
        # 建立一个表达式
        lex = LinearExpr()
        for node_id in vr:
            y = mesh.get_node(node_id).pos[1]
            lex.add(node_id * 2 + 1, 0.5 / dist)
            lex.c -= y * 0.5 / dist
        for node_id in vl:
            y = mesh.get_node(node_id).pos[1]
            lex.add(node_id * 2 + 1, -0.5 / dist)
            lex.c += y * 0.5 / dist
        # 完成
        lex.merge()
        result.append(lex)
    # 每一个元素都是一个线性表达式
    return result


def create_face_xy(mesh):
    """
    用以计算各个face在xy方向上应变的线性表达式.
    """
    assert isinstance(mesh, Mesh3)
    result = []
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        # 分别找到左侧和右侧的两个node
        vl = []
        vr = []
        x_center = face.pos[0]
        for node in face.nodes:
            assert isinstance(node, Mesh3.Node)
            if node.pos[0] > x_center:
                vr.append(node.index)
            else:
                vl.append(node.index)
        assert len(vl) == 2 and len(vr) == 2
        # 两侧的中心距离
        dist = point_distance(get_center(mesh.get_node(vl[0]).pos, mesh.get_node(vl[1]).pos),
                              get_center(mesh.get_node(vr[0]).pos, mesh.get_node(vr[1]).pos))
        # 建立一个表达式
        lex = LinearExpr()
        for node_id in vr:
            y = mesh.get_node(node_id).pos[1]
            lex.add(node_id * 2 + 1, 0.5 / dist)
            lex.c -= y * 0.5 / dist
        for node_id in vl:
            y = mesh.get_node(node_id).pos[1]
            lex.add(node_id * 2 + 1, -0.5 / dist)
            lex.c += y * 0.5 / dist

        # 分别找到左侧和右侧的两个node
        vl = []
        vr = []
        y_center = face.pos[1]
        for node in face.nodes:
            assert isinstance(node, Mesh3.Node)
            if node.pos[1] > y_center:
                vr.append(node.index)
            else:
                vl.append(node.index)
        assert len(vl) == 2 and len(vr) == 2
        # 两侧的中心距离
        dist = point_distance(get_center(mesh.get_node(vl[0]).pos, mesh.get_node(vl[1]).pos),
                              get_center(mesh.get_node(vr[0]).pos, mesh.get_node(vr[1]).pos))
        # 建立一个表达式
        lex = LinearExpr()
        for node_id in vr:
            x = mesh.get_node(node_id).pos[0]
            lex.add(node_id * 2, 0.5 / dist)
            lex.c -= x * 0.5 / dist
        for node_id in vl:
            x = mesh.get_node(node_id).pos[0]
            lex.add(node_id * 2, -0.5 / dist)
            lex.c += x * 0.5 / dist
        # 完成
        lex.merge()
        result.append(lex)
    # 每一个元素都是一个线性表达式
    return result
