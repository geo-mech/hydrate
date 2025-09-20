from zmlx import *

# 进行因素分析的时候，可变变量的数量，应该等于函数run的参数的数量(注意，这个变量的数量不能为0)
n_vari = 2


def run_case(x, y):
    """
    内核函数，用于在给定的参数下计算 （运行一个case）
    """
    # 根据给定的参数x和y，设置一个文件夹，用于数据的输出
    folder = os.path.join(os.getcwd(), 'result', f'{x} {y}')

    # 在目录folder下，输出一个文件
    with open(make_parent(os.path.join(folder, 'result.txt')), 'w') as file:
        file.write(f'x = {x}, y = {y}')


def main(argv):
    """
    主函数，用来调用计算内核
    """
    if len(argv) == 1:
        for x in np.linspace(0, 1, 10):
            for y in np.linspace(3, 4, 5):
                print(f'x = {x}, y={y}')
                sbatch(argv[0], x, y, c=2, t=1)

    if len(argv) == n_vari + 1:
        run_case(float(argv[1]), float(argv[2]))


if __name__ == '__main__':
    main(sys.argv)
