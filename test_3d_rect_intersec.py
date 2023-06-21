from zmlx.alg.dfn_v3 import *
from zmlx.alg.rectangle_intersect_3d import *
# 创建矩形（都是竖直方向的矩形）
fractures = create_demo()

links = create_links(fractures)
print(f'count of links: {len(links)} (有多少对矩形之间存在共有的线段)')

# 转化为一系列三维矩形
# 每一个矩形用9个数字表示 （矩形中心坐标、相邻两个边的坐标）

rc3 = to_rc3(fractures)

num = 0
for i in range(len(rc3)):
    for j in range(i + 1, len(rc3)):
        intersec = calculate_3d_rectangle_intersect(
            (rc3[i][0], rc3[i][1], rc3[i][2]),
            (rc3[i][3], rc3[i][4], rc3[i][5]),
            (rc3[i][6], rc3[i][7], rc3[i][8]),
            (rc3[j][0], rc3[j][1], rc3[j][2]),
            (rc3[j][3], rc3[j][4], rc3[j][5]),
            (rc3[j][6], rc3[j][7], rc3[j][8]))
        if intersec is not None:
            #print(i, j)
            num += 1
print(i)
