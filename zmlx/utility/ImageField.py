
class ImageField:
    def __init__(self, fname, normal_dir, xrange, yrange, crange):
        """
        fname：文件名 （可以是一个图片，也可以是包含几列数的txt文件）
        normal_dir: 法线方向：0 和x垂直；1和y轴垂直；2：和z垂直;
        xrange: 包含2个数，图片原始坐标下，在宽度方向，代表的实际坐标的范围
        yrange: 包含2个数，图片原始坐标下，在高度方向，代表的实际坐标的范围
        crange: 包含2个数。图片灰度返回[0,255]之间的数值，代表了[vmin, vmax]之间的物理变量
        """
        self.crange = crange

        """
                给定位置参数，返回这个地方的值:

                关于插值：
                https://zhuanlan.zhihu.com/p/136700122 
                
        1、读取图片，做成三列数  i   j   gray
        2。 根据xrange, yrange，把它转化成  x   y  gray
        3. 根据 crange，把转化成  x   y  value
        4. 调用 https://zhuanlan.zhihu.com/p/136700122 ，生成插值体
                """
        self.interp = None

    def __call__(self, x, y, z):
        """
        给定位置参数，返回这个地方的值:

        关于插值：
        https://zhuanlan.zhihu.com/p/136700122

        5. x, y, z ，根据normal_dir，删掉一个坐标，成为两个
        5. 读取插值提，获得 (x, y)位置的数值.
        """
        return self.interp.get(x, y)  # 'nearest' 找到数值
        # gray = 100
        # return (100 / 255) * (self.crange[1] - self.crange[0]) + self.crange[0]



