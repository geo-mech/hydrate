from zmlx.alg.load_col import load_col
import os

# 文件路径
fpath = os.path.join(os.path.dirname(__file__), 'example.fn2')

# 裂缝位置
pos = load_col(fpath, index=[0, 1, 2, 3])

# 裂缝宽度
w = load_col(fpath, 4)

# 裂缝颜色
c = load_col(fpath, 6)

if __name__ == '__main__':
    print(pos)
    print(w)
    print(c)
