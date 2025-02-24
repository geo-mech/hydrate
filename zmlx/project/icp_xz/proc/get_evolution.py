import numpy as np

from zml import Seepage
from zmlx.config import seepage
from zmlx.utility.SeepageNumpy import as_numpy
import os
from zmlx.alg.apply_async import create_async, apply_async


def mean_of_top_percentile(arr, percentile):
    # 计算要选择的元素数量
    k = int(len(arr) * percentile)

    # 对数组进行排序
    sorted_arr = np.sort(arr)

    # 选择最大的 k 个元素
    top_elements = sorted_arr[-k:]

    # 计算所选元素的平均值
    mean_top_percentile = np.mean(top_elements)

    return mean_top_percentile


def count_elements_greater_than(arr, value):
    # 创建布尔数组，True 表示元素大于 value
    mask = arr > value

    # 使用布尔数组计算大于 value 的元素个数
    count = np.count_nonzero(mask)

    return count


def get_evolution(folder):
    """
    给定工作的主目录，来获得随着温度、物质等随着时间的演化. 数据格式为：
        Years, t_average, t_max, ratio, kg, ho, lo, ch4, steam, h2o, p_average, p_max
    """
    data = []
    for name in os.listdir(os.path.join(folder, 'models')):
        print(f'name = {name}. ', end='')
        # Load model
        model = Seepage(path=os.path.join(folder, 'models', name))

        # 模型的时间
        time = seepage.get_time(model) / (24*3600*365)

        # 读取平均的温度
        temp = as_numpy(model).cells.get(model.get_cell_key('temperature'))
        temp = temp[: -1]  # 去除最后一个虚拟的

        t_average = np.mean(temp)
        t_max = mean_of_top_percentile(temp, 0.03)   # 待定的变量为这个比例

        # 加热的比例
        ratio = count_elements_greater_than(temp, 565.0) / len(temp)

        # 下面，读取储层内物质的质量
        field_mass = [np.sum(as_numpy(model).fluids(*model.find_fludef(name)).mass[: -1]) / 1000.0
                      for name in ['kg', 'ho', 'lo', 'ch4', 'steam', 'h2o']]

        # 下面，读取压力
        pre = as_numpy(model).cells.pre
        pre = pre[: -1]
        p_average = np.mean(pre)
        p_max = mean_of_top_percentile(pre, 0.03)

        print(f'time = {time}, t_ave = {t_average}, t_max = {t_max}, ratio = {ratio}, mass = {field_mass}')

        # 记录数据
        data.append([time, t_average, t_max, ratio] + field_mass + [p_average, p_max])

    # 形成一个矩阵
    data = np.vstack(data)

    # 写入文件
    np.savetxt(os.path.join(folder, 'evolution.txt'), data)
    print('Succeed!!')


def find_models_folders(root_folder):
    models_folders = []

    for root, dirs, files in os.walk(root_folder):
        if 'models' in dirs:
            models_folder_path = os.path.join(root, 'models')
            models_folders.append(models_folder_path)

    return models_folders


def proc_all(root):
    """
    处理路径下所有的内容
    """
    folders = find_models_folders(root)
    tasks = []
    for item in folders:
        folder = os.path.dirname(item)
        print(folder)
        tasks.append(create_async(func=get_evolution, args=[folder]))
    apply_async(tasks=tasks)


if __name__ == '__main__':
    pass
