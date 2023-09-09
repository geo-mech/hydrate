# ** desc = '用以展示timer的使用方法'

from zml import timer, clock, gui
from time import sleep


# 利用zml.clock修饰的函数在调用的时候会被自动纳入计时
@clock
def xxx(seconds):
    sleep(seconds)


def test():
    for i in range(10):
        gui.break_point()
        print(i)

        # 方法1：利用timer来调用需要被计时的函数
        timer('proc_1', sleep, 0.1)

        # 方法2：将需要计时的部分，放入timer.beg(name)和timer.end()之间
        timer.beg('proc_2')
        sleep(0.1)
        timer.end('proc_2')

        # 方法3：调用zml.clock修饰的函数
        xxx(0.1)

    print(timer)


if __name__ == '__main__':
    test()
