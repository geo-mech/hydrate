# ** desc = '测试，恒定压力作用下，裂缝的宽度'

from zml import DDMSolution2, InfMatrix, FractureNetwork, FracAlg
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

    # 添加裂缝
    FracAlg.add_frac(network, p0=[-50, 0], p1=[50, 0], lave=1.0)

    # 设置裂缝的属性，特别地，裂缝内压力设置为1MPa
    for f in network.fractures:
        f.p0 = 1.0e6
        f.k = 0
        f.h = 1e4  # 相当于无穷高

    # 更新应力影响矩阵
    matrix.update(network, sol2)
    # 使用最新的矩阵，更新裂缝的位移
    FracAlg.update_disp(network=network, matrix=matrix)

    # 显示裂缝的位移，并和理论解进行对比
    for f in network.fractures:
        x0, y0, x1, y1 = f.pos
        pos = mean(x0, x1)
        width = get_frac_width(pos, half_length=50,
                               shear_modulus=sol2.shear_modulus,
                               poisson_ratio=sol2.poisson_ratio,
                               fluid_net_pressure=1e6)
        print(f'{pos}\t {width}\t {f.dn}')


if __name__ == '__main__':
    main()
