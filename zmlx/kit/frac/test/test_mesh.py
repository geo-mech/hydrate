"""
裂缝对应的渗流网络
"""
from zml import FractureNetwork
from zmlx.kit.frac.create_seepage_mesh import create_seepage_mesh


def test():
    """
    测试函数
    """
    network = FractureNetwork()
    network.add_fracture(first=[0, 0], second=[10, 0], lave=0.5)
    print(network)
    mesh = create_seepage_mesh(network, 1, 1, 1)
    print(mesh)


if __name__ == '__main__':
    test()
