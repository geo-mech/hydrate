from zml import SeepageMesh


def scale(mesh: SeepageMesh, factor: float, on_pos=True, on_area=True, on_vol=True, on_dist=True):
    """
    对渗流的网格进行缩放.
    """
    if on_pos or on_vol:
        for cell in mesh.cells:
            assert isinstance(cell, SeepageMesh.Cell)
            if on_pos:
                pos = [v * factor for v in cell.pos]
                cell.pos = pos
            if on_vol:
                cell.vol *= factor ** 3

    if on_area or on_dist:
        for face in mesh.faces:
            assert isinstance(face, SeepageMesh.Face)
            if on_area:
                face.area *= factor ** 2
            if on_dist:
                face.dist *= factor

    return mesh
