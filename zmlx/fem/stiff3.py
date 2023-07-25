from zml import *
from zmlx.fem.cube2tet import cube2tet
from zmlx.fem.stiffness_tet4 import stiffness as tet4_stiff


def stiff3(body, E, mu):
    """
    创建body的刚度矩阵
    """
    assert isinstance(body, Mesh3.Body)
    assert body.node_number == 4 or body.node_number == 8
    if body.node_number == 4:
        assert body.link_number == 6
        assert body.face_number == 4
        x0, y0, z0 = body.get_node(0).pos
        x1, y1, z1 = body.get_node(1).pos
        x2, y2, z2 = body.get_node(2).pos
        x3, y3, z3 = body.get_node(3).pos
        stiff = tet4_stiff(x0, x1, x2, x3, y0, y1, y2, y3, z0, z1, z2, z3, E=E, mu=mu)
        if stiff[0, 0] >= 0:
            return stiff
        else:
            return -stiff
    else:
        assert body.link_number == 12
        assert body.face_number == 6
        mat = np.zeros(shape=(24, 24), dtype=float)
        tets = cube2tet(body, to_local=True)
        for i0, i1, i2, i3 in tets:
            x0, y0, z0 = body.get_node(i0).pos
            x1, y1, z1 = body.get_node(i1).pos
            x2, y2, z2 = body.get_node(i2).pos
            x3, y3, z3 = body.get_node(i3).pos
            stiff = tet4_stiff(x0, x1, x2, x3, y0, y1, y2, y3, z0, z1, z2, z3, E=E, mu=mu)
            if stiff[0, 0] < 0:
                stiff = -stiff
            inds = [i0 * 3, i0 * 3 + 1, i0 * 3 + 2,
                    i1 * 3, i1 * 3 + 1, i1 * 3 + 2,
                    i2 * 3, i2 * 3 + 1, i2 * 3 + 2,
                    i3 * 3, i3 * 3 + 1, i3 * 3 + 2]
            ix_ = np.ix_(inds, inds)
            mat[ix_] = mat[ix_] + stiff
        return mat
