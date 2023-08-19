from zml import Timer, timer

__all__ = ['Timer', 'timer']


def test():
    """
    用以展示timer的使用方法
    """
    from time import sleep

    for i in range(3):
        print(i)

        timer('0', sleep, 0.01)
        timer(1, sleep, 0.02)

        timer.beg(2)
        sleep(0.1)
        timer.end(2)

        timer.beg('3')
        sleep(0.1)
        timer.end('3')

    print(timer)


if __name__ == '__main__':
    test()
