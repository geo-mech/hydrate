from zml import *
from zmlx.io.path import get_path as opath


def main():
    # 默认的裂缝数据
    fracture = FractureNetwork.FractureData()
    fracture.p0 = 1e6
    fracture.k = 0

    # 裂缝网络
    network = FractureNetwork()
    network.add_fracture(pos=[-20, 0, 8, 0], lave=0.1, data=fracture)
    print(network)

    # 弹性参数
    sol2 = DDMSolution2()

    # 影响系数矩阵
    matrix = InfMatrix()
    matrix.update(network, sol2=sol2)

    # 更新位移
    network.update_disp(matrix=matrix)

    # 生成数据
    r = np.linspace(0.0, 1.0, 30)
    x = np.linspace(0.0, 10.0, 100)
    rv, xv = np.meshgrid(r, x)
    vv = np.zeros(rv.shape)
    buf = Tensor2()
    for i0 in range(vv.shape[0]):
        print(f'i0 = {i0}')
        for i1 in range(vv.shape[1]):
            r = rv[i0, i1]
            x = xv[i0, i1]
            network.get_induced(pos=[x, r], sol2=sol2, buf=buf)
            vv[i0, i1] = buf.yy

    if opath() is not None:
        np.savetxt(opath('rv.txt'), rv)
        np.savetxt(opath('xv.txt'), xv)
        np.savetxt(opath('vv.txt'), vv)
        print(f'data saved to folder: {opath()}')
    else:
        print('output path not set')


if __name__ == '__main__':
    main()
