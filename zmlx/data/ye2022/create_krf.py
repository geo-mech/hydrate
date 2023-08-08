from zmlx.kr.create_krf import create_krf


def run():
    x, y = create_krf(0.2, 3)
    with open('krf.txt', 'w') as file:
        for i in range(len(x)):
            file.write(f'{x[i]}   {y[i]} \n')


if __name__ == '__main__':
    run()
