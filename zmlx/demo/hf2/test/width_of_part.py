from zml import DDMSolution2, InfMatrix, FractureNetwork, Tensor2
from zmlx.demo.hf2.set_insitu_stress import set_insitu_stress


def main():
    """
    计算恒定压力下裂缝的位移，并且和理论解进行对比
    """
    # 创建数据
    network = FractureNetwork()
    sol2 = DDMSolution2()
    matrix = InfMatrix()
    fa_yy = 0
    fa_xy = 1
    fa_keep = 2

    # 添加裂缝
    network.add_fracture(pos=[-50, 0, 50, 0], lave=1.0)

    # 设置裂缝的属性，特别地，裂缝内压力设置为1MPa
    for f in network.fractures:
        assert isinstance(f, FractureNetwork.Fracture)
        f.p0 = 1.0e6
        f.k = 0
        f.h = 1e4  # 相当于无穷高
        if f.center[0] > 0:
            f.set_attr(fa_keep, 1)

    set_insitu_stress(network, fa_yy=fa_yy, fa_xy=fa_xy,
                      stress=lambda x, y: Tensor2(0, -0.99e6, 0.5e6))

    # 创建一个子网络，只保留需要计算的部分
    sub_network = network.get_sub_network(fa_key=fa_keep)

    # 更新应力影响矩阵
    matrix.update(sub_network, sol2)
    # 使用最新的矩阵，更新裂缝的位移
    sub_network.update_disp(matrix=matrix, fa_yy=fa_yy, fa_xy=fa_xy)

    # 更新之后，再返回来
    network.copy_fracture_from_sub_network(
        fa_key=fa_keep,
        sub=sub_network)

    # 显示裂缝的位移
    for f in network.fractures:
        print(f'{f.center[0]}\t   {f.dn}\t   {f.ds}')


if __name__ == '__main__':
    main()
