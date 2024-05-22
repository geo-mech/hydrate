from zml import SeepageMesh
from zmlx.seepage_mesh.ascii import load_ascii


def load_mesh(cellfile=None, facefile=None, path=None):
    """
    从文件中读取Mesh文件
    """
    mesh = SeepageMesh()
    if path is not None:
        assert cellfile is None and facefile is None
        mesh.load(path)
    else:
        assert cellfile is not None and facefile is not None
        load_ascii(cellfile, facefile, mesh=mesh)
    return mesh
