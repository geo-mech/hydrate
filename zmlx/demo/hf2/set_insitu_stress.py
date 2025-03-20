from zml import FractureNetwork, Tensor2


def set_insitu_stress(network: FractureNetwork, fa_yy, fa_xy, stress):
    """
    设置内应力
    Args:
        stress: 原始的地应力，应该是一个Tensor2，或者是一个位置x和y的函数，且函数返回一个Tensor2
        network: 需要设置的裂缝网络
        fa_xy: 存储局部剪切应力的属性
        fa_yy: 存储局部的法向应力的属性
    """
    local_stress = Tensor2()
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.Fracture)

        if callable(stress):
            temp = stress(*fracture.center)
        else:
            temp = stress

        if isinstance(temp, Tensor2):
            temp.get_rotate(fracture.angle, buffer=local_stress)
            fracture.set_attr(fa_xy, local_stress.xy)
            fracture.set_attr(fa_yy, local_stress.yy)
        else:
            fracture.set_attr(fa_xy, 0)
            fracture.set_attr(fa_yy, 0)


def test():
    network = FractureNetwork()
    network.add_fracture(first=[0, 0], second=[-1, 0.001], lave=0.1)
    set_insitu_stress(network,
                      0,
                      1, Tensor2(xx=1, yy=2, xy=0))
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.Fracture)
        print(fracture.get_attr(0), fracture.get_attr(1))


if __name__ == '__main__':
    test()
