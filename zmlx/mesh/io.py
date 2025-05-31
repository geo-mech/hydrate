from zml import Mesh3


def load_trimesh(node_file, triangle_file, i_beg=0):
    """
    利用节点node文件（包含2或者3列，为node的位置）和三角形文件<包含三列，为三角形的编号>
    """
    mesh = Mesh3()

    with open(node_file, 'r') as file:
        for line in file.readlines():
            values = [float(w) for w in line.split()]
            if len(values) > 0:
                pos = []
                for i in range(3):
                    if i < len(values):
                        pos.append(values[i])
                    else:
                        pos.append(0)
                mesh.add_node(*pos)

    with open(triangle_file, 'r') as file:
        for line in file.readlines():
            values = [float(w) for w in line.split()]
            if len(values) == 3:
                nodes = [mesh.get_node(round(x - i_beg)) for x in values]
                l01 = mesh.add_link(nodes=[nodes[0], nodes[1]])
                l12 = mesh.add_link(nodes=[nodes[1], nodes[2]])
                l20 = mesh.add_link(nodes=[nodes[2], nodes[0]])
                mesh.add_face(links=[l01, l12, l20])

    return mesh
