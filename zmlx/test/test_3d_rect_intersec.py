from zmlx.alg.dfn_v3 import *
from zmlx.alg.rectangle_intersect_3d import *
import numpy as np
# 创建矩形（都是竖直方向的矩形）
fractures = create_demo()

links = create_links(fractures)

print(f'count of links: {len(links)} (有多少对矩形之间存在共有的线段)')

# 保存相交矩形序号
np.savetxt('hydrate/zmlx/alg/rectangle_intersect_3d_test/demo_links.txt', links, fmt='%4d')

# 转化为一系列三维矩形
# 每一个矩形用9个数字表示 （矩形中心坐标、相邻两个边的坐标）
rc3 = to_rc3(fractures)

# 保存相交矩形顶点坐标
np.savetxt('hydrate/zmlx/alg/rectangle_intersect_3d_test/vertices.txt', rc3, fmt='%05f')

num = 0
test_links = []
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
            # print(i, j)
            test_links.append([i,j])
            num += 1

# 保存计算得到相交矩形序号
np.savetxt('hydrate/zmlx/alg/rectangle_intersect_3d_test/cal_links.txt', np.array(test_links),fmt='%4d') 

# 输出计算得到相交对数
print(f'计算得到相交矩形对数{num}')
