from zml import Mesh3, np
from zmlx.fem.cube2tet import cube2tet
from zmlx.fem.elements.c3d4 import stiffness


def stiff3(body, E, mu):
    """
    创建body的刚度矩阵
    """
    assert isinstance(body, Mesh3.Body)
    assert body.node_number == 4 or body.node_number == 8
    if body.node_number == 4:
        assert body.link_number == 6
        assert body.face_number == 4
        nodes = [node.pos for node in body.nodes]
        stiff = stiffness(nodes, E=E, mu=mu)
        assert stiff[0, 0] >= 0
        return stiff
    else:
        assert body.link_number == 12
        assert body.face_number == 6
        mat = np.zeros(shape=(24, 24), dtype=float)
        tets = cube2tet(body, to_local=True)
        for i0, i1, i2, i3 in tets:
            nodes = [body.get_node(i).pos for i in [i0, i1, i2, i3]]
            stiff = stiffness(nodes, E=E, mu=mu)
            if stiff[0, 0] < 0:
                stiff = -stiff
            inds = [i0 * 3, i0 * 3 + 1, i0 * 3 + 2,
                    i1 * 3, i1 * 3 + 1, i1 * 3 + 2,
                    i2 * 3, i2 * 3 + 1, i2 * 3 + 2,
                    i3 * 3, i3 * 3 + 1, i3 * 3 + 2]
            ix_ = np.ix_(inds, inds)
            mat[ix_] = mat[ix_] + stiff
        return mat
