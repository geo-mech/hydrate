# ** desc = '用以展示timer的使用方法'
#
# 本示例演示zmlx库中timer工具的使用方法，用于代码性能分析和计时。
# timer提供了三种计时方式：
#   1. 直接调用timer(name, func, *args)对函数执行进行计时；
#   2. 使用timer.beg(name)和timer.end(name)手动标记代码块的起止；
#   3. 使用@clock装饰器自动对函数进行计时。
# 三种方式均可精确测量代码执行时间，便于性能优化分析。
# 运行结束后，在GUI模式下可调用gui.show_timer()显示计时结果。

from time import sleep

from zmlx import *


# 利用zml.clock修饰的函数在调用的时候会被自动纳入计时
@clock  # @clock装饰器自动对该函数进行计时，每次调用都会记录耗时
def xxx(seconds):
    """
    使用@clock装饰器自动计时的示例函数。

    该函数仅执行sleep操作，用于演示装饰器自动计时功能。
    每次调用都会自动记录执行时间并在timer中累加。

    Args:
        seconds: 休眠的秒数（即模拟的工作耗时）。
    """
    sleep(seconds)


def test():
    """
    测试函数：演示三种计时方式。

    在10次循环中，分别使用三种计时方法对sleep(0.1)进行计时：
    - timer函数调用计时
    - timer.beg/end代码块计时
    - @clock装饰器自动计时
    循环结束后打印计时汇总结果，并在GUI模式下显示。

    Returns:
        无返回值。
    """
    for i in range(10):
        gui.break_point()
        print(i)

        # 方法1：利用timer来调用需要被计时的函数（直接包裹函数调用）
        timer('proc_1', sleep, 0.1)

        # 方法2：将需要计时的部分，放入timer.beg(name)和timer.end()之间（手动标记起止）
        timer.beg('proc_2')
        sleep(0.1)
        timer.end('proc_2')

        # 方法3：调用zml.clock修饰的函数（装饰器自动计时）
        xxx(0.1)

    print(timer)  # 打印计时汇总结果
    if gui.exists():
        gui.show_timer()  # GUI模式下弹出计时结果窗口


if __name__ == '__main__':
    test()
