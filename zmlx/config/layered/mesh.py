"""
管理多层的渗流网格。
"""
import os

from zmlx import SeepageMesh, make_parent, create_cube_seepage_mesh, opath


def get_test_mesh():
    """
    构建一个用于测试的渗流网络
    """
    import numpy as np
    meshes = []
    x = np.linspace(-200, 200, 100)
    y = np.linspace(-100, 100, 50)
    for z in np.linspace(-2000, -1950, 5):
        print(f'z = {z}')
        mesh = create_cube_seepage_mesh(
            x=x,
            y=y,
            z=[z - 1, z + 1]
        )
        meshes.append(mesh)

    return meshes


def _make_path(folder, idx):
    return make_parent(os.path.join(folder, '%03d.seepage_mesh' % idx))


def save_mesh(folder, meshes):
    """
    保存Mesh
    """
    for idx in range(len(meshes) + 1):  # 确保文件不存在
        fname = _make_path(folder, idx)
        if os.path.isfile(fname):
            os.remove(fname)

    for idx, mesh in enumerate(meshes):
        assert isinstance(mesh, SeepageMesh)
        mesh.save(_make_path(folder, idx))


def load_mesh(folder):
    """
    载入Mesh
    """
    meshes = []
    for idx in range(9999):
        fname = _make_path(folder, idx)
        if os.path.isfile(fname):
            mesh = SeepageMesh(path=fname)
            meshes.append(mesh)
        else:
            break

    return meshes


def test():
    meshes = get_test_mesh()

    folder = opath('meshes')
    print(f'folder = {folder}')

    save_mesh(folder, meshes)
    print(load_mesh(folder))


if __name__ == '__main__':
    test()
