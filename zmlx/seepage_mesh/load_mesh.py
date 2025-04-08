from zml import SeepageMesh
from zmlx.seepage_mesh.ascii import load_ascii


def load_mesh(cell_file=None, face_file=None, path=None):
    """
    从文件中读取Mesh文件
    """
    mesh = SeepageMesh()
    if path is not None:
        assert cell_file is None and face_file is None
        mesh.load(path)
    else:
        assert cell_file is not None and face_file is not None
        load_ascii(cell_file, face_file, mesh=mesh)
    return mesh
