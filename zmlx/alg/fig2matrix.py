import numpy as np
import cv2
import matplotlib.pyplot as plt


def fig2matrix(fig_path, cm_path, c_min=0, c_max=1, transfunc='linear', errorlimit=1000, mend=False):
    """
    将jx*jy像素的图片<多通道的彩图>转化为jx*jy大小的矩阵，其中矩阵的元素数值根据图片的颜色和颜色表指定。

    :param fig_path:   原始图片的路径
    :param cm_path:    原始颜色表的路径
    :param c_min:      颜色表中对应的最小值，默认值为0
    :param c_max:      颜色表中对应的最大值，默认值为1
    :param transfunc:  原始颜色表的坐标轴方式，目前支持"linear"和"log10"两种，默认选择"linear"模式
    :param errorlimit: 误差限制，误差超过限制后，识别数据会被替换为-1，默认值为1000，即不采取替换操作
    :param mend:       是否启用修复功能，输入参数为True或False，启用后修复被标记为-1的错误数值，默认参数为False
    :return:           二维的numpy数组，数组的大小和原图片保持一致。

        版本号v1.2
        by 陈薪硕  2023年6月21日
    """

    # 读取并制作色标和真值的映射关系（颜色表），输出形式为二维数组，行数为色标长度，列数为RGB+真值共4列
    colorbar = cv2.imread(cm_path)
    valuebar = __makemappingcode(colorbar, c_min, c_max, transfunc)

    # 读取云图，输出三维数组，长×宽×3（RGB三通道）
    contour = cv2.imread(fig_path)
    contour = cv2.flip(contour, 0)  # cv2读取图片有可能颠倒，若颠倒，则需要该行代码颠倒回去。有可能是cv2库的问题。
    l, w, h = contour.shape

    # 云图像素的数据映射,分别输出真值和误差的二维数组，两个数组均与原图尺寸一致
    valuelist = []
    errorlist = []
    for pixline in contour:
        for pixel in pixline:
            truevalue, error = __color2value(pixel, valuebar, errorlimit)
            valuelist.append(truevalue)
            errorlist.append(error)  # 先输出一维的list
    datamatrix0 = np.asarray(valuelist).reshape(l, w)
    errormatrix = np.asarray(errorlist).reshape(l, w)  # 将list转换成numpy二维数组
    if mend:
        datamatrix = __menddata(datamatrix0)  # 修补数据
    else:
        datamatrix = datamatrix0
    print('transdata finished')
    return datamatrix, errormatrix


def __makemappingcode(bar, c_min, c_max, transfunc):  # 辅助函数1
    """
    输入colorbar矩阵，输出颜色映射数组（颜色表）

    :param bar:         colorbar图像，要求水平放置，最小值在左侧，最大值在右侧
    :param c_min:       colorbar代表的最小值
    :param c_max:       colorbar代表的最大值
    :param transfunc:   原始colorbar的坐标轴方式，目前支持"linear"和"log10"两种
    :return:            返回列数为4的二维数组，前3列为bgr值，第4列为对应的真实数据
    """

    barmean = np.mean(bar, 0)
    if transfunc == 'linear':
        intensity = np.linspace(c_min, c_max, num=barmean.shape[0])
        intensity = np.expand_dims(intensity, axis=1)
        TrueValueBar = np.hstack((barmean, intensity))
    elif transfunc == 'log10':
        index = np.linspace(np.log10(c_min), np.log10(c_max), num=barmean.shape[0])
        intensity = 10 ** index
        intensity = np.expand_dims(intensity, axis=1)
        TrueValueBar = np.hstack((barmean, intensity))
    else:
        print("I don't know how to process the cm data.")
        TrueValueBar = []
    return TrueValueBar


def __color2value(bgrnum, ValueBar, errorlimit):  # 辅助函数2
    """
    将单个像素点的rgb数据转换成真实数据

    :param bgrnum:      像素点原始的bgr数据，1*3数组
    :param ValueBar:    颜色表，4列的二维数组，由其他函数输出
    :param errorlimit:  误差限制，误差超过限制后，识别数据会被替换为-1
    :return:            返回值为该像素点的真实数据，以及该像素点的识别误差，两个单独的数字
    """

    # 先进行数据有效性检验，目前仅检验是否为1*3向量
    if bgrnum.shape == np.asarray(3):

        # 在色标上一一比对，计算颜色最小偏差，并索引回色标，找到对应的真值
        color_diff = []
        for color in ValueBar:
            bdiff = bgrnum[0] - color[0]
            gdiff = bgrnum[1] - color[1]
            rdiff = bgrnum[2] - color[2]
            diff = rdiff ** 2 + gdiff ** 2 + bdiff ** 2
            color_diff.append(diff)
        index = color_diff.index(min(color_diff))
        error = min(color_diff) ** (1 / 3)
        if error < errorlimit:
            value = ValueBar[index][3]
        else:
            value = -1
            error = -1 * error
        return value, error
    else:
        print('color2value input invalid!')


def __menddata(figinput):  # 辅助函数3
    """
    修复二维数据中识别失败的值（已被标记为-1），修复计算参照错误数据周围的四个位置的数据。
    周围四个数据中有两个以上有效时，才会启用修复功能。

    :param figinput:    需要被修复的数据
    :return:            修复后的二维数据
    """

    # 输入与错误查找
    fig0 = figinput
    fig1 = figinput.copy()
    err = np.argwhere(fig0 == -1)
    # 当错误索引不为空时，持续进行填补
    while err.size > 0:
        marki = -1
        marklist = []
        # 对错误索引中的位置循环操作，一轮一轮填补该轮可以填补的像素
        # 判断目标像素四周是否valid，两个以上时才进行填补
        for position in err:
            marki = marki + 1
            x0, x1 = position
            near = np.zeros(4)  # [up, right, down, left] 真值
            nearif0 = np.asarray([x0, x1, x0, x1])
            nearif1 = np.asarray([0, fig0.shape[1] - 1, fig0.shape[0] - 1, 0])
            nearjudge1 = nearif0 == nearif1
            near[0] = -1 if nearjudge1[0] else fig0[x0 - 1][x1]
            near[1] = -1 if nearjudge1[1] else fig0[x0][x1 + 1]
            near[2] = -1 if nearjudge1[2] else fig0[x0 + 1][x1]
            near[3] = -1 if nearjudge1[3] else fig0[x0][x1 - 1]
            validnum = 4 - np.sum(near == -1)
            if validnum > 1:  # 判断周围有两个及以上有效数据时，才修补
                for i in range(near.size):
                    near[i] = 0 if near[i] == -1 else near[i]
                fig1[x0][x1] = np.sum(near) / validnum  # 区分fig0和fig1是为了将每一轮修补区分开，提高修补准确性
                marklist.append(marki)
        mark = np.asarray(marklist)
        err = np.delete(err, mark, axis=0)
        fig0 = fig1.copy()
    return fig0


if __name__ == '__main__':  # 测试用代码
    # result, erro = fig2matrix('eg02/eg02inputfig.png', 'eg02/eg02inputcm.png', c_min=0, c_max=255, transfunc='linear',
    #                           errorlimit=1000)
    result, erro = fig2matrix('test.png', 'inputcm.png', c_min=0, c_max=255, transfunc='linear',
                              errorlimit=30, mend=False)
    x = np.linspace(0, result.shape[1] - 1, result.shape[1])
    y = np.linspace(0, result.shape[0] - 1, result.shape[0])
    fig = plt.figure(figsize=(15, 15), dpi=200)  # 调整图幅
    # result = np.log10(np.absolute(result))  # 对数识别时绘图测试需再转换一次
    plt.contourf(x, y, result, 500, cmap=plt.cm.jet)
    plt.savefig('resulteg01.png', dpi=200)
