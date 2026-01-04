from zmlx.fig.plt_render.dfn2 import add_dfn2


def get_edges(triangles, points):
    edges = set()
    for tri in triangles:
        assert len(tri) == 3, f'The size of tri must be 3, but got: ({tri})'
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            if a > b:
                a, b = b, a
            edges.add((a, b))
    return [[points[a][0], points[a][1], points[b][0], points[b][1]] for a, b in edges]


def add_trimesh(ax, triangles, points, **opts):
    add_dfn2(ax, get_edges(triangles, points), **opts)
