"""
说明：
    将这个脚本放到models旁边（models里面，存储了solve之后的Seepage文件）
    修改脚本里面的监测点，然后，运行，即可生成一个文件，这个文件包含两列
    第一列是时间，第二列是给定位置的压力.
"""
from zmlx import *   # 需要首先确保zmlx可用


def main():
    target_index = None

    time_to_pressure = []

    for name in os.listdir('models'):
        print(name)
        model = Seepage(path=os.path.join('models', name))
        if target_index is None:
            target_index = model.get_nearest_cell(pos=(10, 0, 0)).index
        pressure = model.get_cell(target_index).pre
        time_to_pressure.append([seepage.get_time(model), pressure])

    np.savetxt('time_to_pressure.txt', time_to_pressure)


if __name__ == '__main__':
    main()
