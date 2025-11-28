# ** desc = '创建Mesh3'

from zmlx import *


def main():
    mesh = Mesh3()

    # 第一步，添加节点
    mesh.add_node(0, 0, 0)
    mesh.add_node(1, 0, 0)
    mesh.add_node(0, 1, 0)
    mesh.add_node(0, 0, 1)

    # 第二步，添加线(因为后续在添加面的时候，也在添加Link，因此，这一步可以省略)
    mesh.add_link([0, 1])
    mesh.add_link([0, 2])
    mesh.add_link([0, 3])
    mesh.add_link([1, 2])
    mesh.add_link([1, 3])
    mesh.add_link([2, 3])

    # 第三步，添加面
    mesh.add_face([
        mesh.add_link([1, 2]),
        mesh.add_link([2, 3]),
        mesh.add_link([1, 3])])
    mesh.add_face([
        mesh.add_link([0, 2]),
        mesh.add_link([2, 3]),
        mesh.add_link([0, 3])])
    mesh.add_face([
        mesh.add_link([1, 0]),
        mesh.add_link([0, 3]),
        mesh.add_link([1, 3])])
    mesh.add_face([
        mesh.add_link([1, 2]),
        mesh.add_link([2, 0]),
        mesh.add_link([1, 0])])

    # 第四步，添加体
    mesh.add_body([0, 1, 2, 3])

    # 成功，保存到文件
    mesh.save('mesh.xml')
    print('成功，保存到文件：mesh.xml')


if __name__ == '__main__':
    main()
