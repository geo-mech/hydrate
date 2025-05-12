import math

from zml import Mesh3, np


def create_ring(vr, angle_step=math.pi / 20.0, z=0.0):
    """
    建立一个圆环在极坐标下的规则网格.  这里，仍然采用Mesh3的形式返回，但是，其中的x代表半径，y代表角度，z为给定的数值. 因此，Mesh3关于中心
    体积、面积等的属性，对于这里返回的mesh均不适用.
    """
    ja = max(round(math.pi * 2.0 / angle_step), 1) + 1

    # 半径的node
    assert len(vr) >= 2

    # 角度的node
    va = np.linspace(0, math.pi * 2, ja)

    mesh = Mesh3()

    # 暂存，将所有的node的ID放入到矩阵中，方便后续建立link
    node_ids = []

    # 添加所有的node
    for ia in range(len(va) - 1):
        node_ids.append([mesh.add_node(x=r, y=va[ia], z=z).index for r in vr])

    # 添加所有的link和face
    for ia in range(len(va) - 1):
        for ir in range(len(vr) - 1):
            n00 = mesh.get_node(node_ids[ia][ir])
            n01 = mesh.get_node(node_ids[ia][ir + 1])
            n10 = mesh.get_node(
                node_ids[ia + 1 if ia + 1 < len(node_ids) else 0][ir])
            n11 = mesh.get_node(
                node_ids[ia + 1 if ia + 1 < len(node_ids) else 0][ir + 1])
            mesh.add_face(links=[mesh.add_link([n00, n10]),
                                 mesh.add_link([n00, n01]),
                                 mesh.add_link([n11, n10]),
                                 mesh.add_link([n11, n01])])

    # 完成
    return mesh


def _test1():
    vr = np.linspace(1.0, 2.0, 20)
    mesh = create_ring(vr)
    print(mesh)


if __name__ == '__main__':
    _test1()
