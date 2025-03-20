from zml import DDMSolution2, InfMatrix, FractureNetwork
from zmlx.alg.get_frac_width import get_frac_width
from zmlx.alg.mean import mean


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

    # 添加裂缝
    network.add_fracture(pos=[-50, 0, 50, 0], lave=1.0)

    # 设置裂缝的属性，特别地，裂缝内压力设置为1MPa
    for f in network.fractures:
        assert isinstance(f, FractureNetwork.Fracture)
        f.p0 = 1.0e6
        f.k = 0
        f.h = 1e4  # 相当于无穷高
        f.set_attr(fa_yy, -0.5e6)
        f.set_attr(fa_xy, 1.0e6)

    # 更新应力影响矩阵
    matrix.update(network, sol2)
    # 使用最新的矩阵，更新裂缝的位移
    network.update_disp(matrix=matrix, fa_yy=fa_yy, fa_xy=fa_xy)

    # 显示裂缝的位移，并和理论解进行对比
    for f in network.fractures:
        x0, y0, x1, y1 = f.pos
        pos = mean(x0, x1)
        width = get_frac_width(
            pos,
            half_length=50,
            shear_modulus=sol2.shear_modulus,
            poisson_ratio=sol2.poisson_ratio,
            fluid_net_pressure=1e6)
        print(f'{pos}\t   {width}\t   {f.dn}\t   {f.ds}')


if __name__ == '__main__':
    main()
