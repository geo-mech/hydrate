"""
预处理工具：从仅含角节点的网格生成含边中点的二次单元网格。

支持：
- 3节点三角形 → 6节点二次三角形 (T6)
- 4节点四边形 → 8节点Serendipity四边形 (Quad8)
"""


def enrich_with_mid_nodes(corner_elements, coords, element_type='t6'):
    """
    将仅含角节点的单元转换为含边中点的二次单元。

    共享边上的中点只创建一次，确保相邻单元的网格连续。

    Parameters
    ----------
    corner_elements : list of list of int
        角节点连通性列表。每个单元按逆时针顺序：
        - 't6': 3个角节点 [c0, c1, c2]
        - 'quad8': 4个角节点 [c0, c1, c2, c3]
    coords : list of tuple (float, float)
        角节点坐标列表 [(x0,y0), ...]。
        此列表会被原地修改（追加中点坐标）。
    element_type : str
        't6'  — 6节点二次三角形
        'quad8' — 8节点Serendipity四边形

    Returns
    -------
    tuple (enriched_elements, coords, mids)
        enriched_elements : 补全后的单元列表，每个单元按正确的二次节点顺序排列。
        coords : 与输入相同的list对象，已追加中点坐标。
        mids : dict, 映射 (min_node, max_node) -> 中点节点索引, 供边界条件等查询使用。
    """
    if element_type not in ('t6', 'quad8'):
        raise ValueError(f"element_type 必须是 't6' 或 'quad8'，当前值: {element_type!r}")

    mids = {}  # (min_a, max_a) -> mid_node_index
    enriched = []

    # 根据单元类型定义需要创建中点的边
    if element_type == 't6':
        edges = [(0, 1), (1, 2), (2, 0)]
        # T6 节点顺序: [c0, c1, c2, mid(0,1), mid(1,2), mid(2,0)]
    else:  # quad8
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        # Quad8 节点顺序: [c0, c1, c2, c3, mid(0,1), mid(1,2), mid(2,3), mid(3,0)]

    for elem in corner_elements:
        node_count = 3 if element_type == 't6' else 4
        if len(elem) != node_count:
            raise ValueError(
                f"element_type='{element_type}' 要求每个角节点单元有 {node_count} 个节点，"
                f"但发现一个单元有 {len(elem)} 个节点: {elem}"
            )

        enriched_elem = list(elem)  # 先复制角节点
        for a, b in edges:
            ca, cb = elem[a], elem[b]
            key = (min(ca, cb), max(ca, cb))
            if key not in mids:
                mids[key] = len(coords)
                ax, ay = coords[ca]
                bx, by = coords[cb]
                coords.append(((ax + bx) / 2.0, (ay + by) / 2.0))
            enriched_elem.append(mids[key])

        enriched.append(enriched_elem)

    return enriched, coords, mids


def enriched_mesh_from_grid(Lx, Ly, Nx, Ny, element_type='t6'):
    """
    从结构化矩形网格参数构建含边中点的二次单元网格。

    Parameters
    ----------
    Lx, Ly : float
        x和y方向的域尺寸。
    Nx, Ny : int
        x和y方向的单元数。
    element_type : str
        't6' — 每个矩形网格拆分为2个T6三角形（左下+右上）
        'quad8' — 每个矩形网格作为一个Quad8四边形

    Returns
    -------
    tuple (coords, corner, enriched_elements)
        coords : 全部节点坐标（角节点 + 中点）。
        corner : dict, 映射 (i,j) -> 角节点索引。
        enriched_elements : 补全后的单元列表。
    """
    if element_type not in ('t6', 'quad8'):
        raise ValueError(f"element_type 必须是 't6' 或 'quad8'，当前值: {element_type!r}")

    dx, dy = Lx / Nx, Ly / Ny

    # 创建角节点
    coords = []
    corner = {}
    for j in range(Ny + 1):
        for i in range(Nx + 1):
            corner[(i, j)] = len(coords)
            coords.append((i * dx, j * dy))

    # 构建角节点单元
    corner_elements = []
    if element_type == 't6':
        for j in range(Ny):
            for i in range(Nx):
                c00 = corner[(i, j)]
                c10 = corner[(i + 1, j)]
                c11 = corner[(i + 1, j + 1)]
                c01 = corner[(i, j + 1)]
                # 三角形1: 左下 (c00, c10, c01)
                corner_elements.append([c00, c10, c01])
                # 三角形2: 右上 (c10, c11, c01)
                corner_elements.append([c10, c11, c01])
    else:  # quad8
        for j in range(Ny):
            for i in range(Nx):
                c00 = corner[(i, j)]
                c10 = corner[(i + 1, j)]
                c11 = corner[(i + 1, j + 1)]
                c01 = corner[(i, j + 1)]
                # 单四边形 (ccw: 左下→右下→右上→左上)
                corner_elements.append([c00, c10, c11, c01])

    # 补全中点
    enriched_elements, coords, _mids = enrich_with_mid_nodes(
        corner_elements, coords, element_type=element_type
    )

    return coords, corner, enriched_elements
