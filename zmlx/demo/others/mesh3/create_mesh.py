# ** desc = '创建Mesh3（三维四面体网格）'
#
# 本示例演示如何使用Mesh3类手动构建一个三维四面体网格。
# Mesh3是zmlx中用于表示三维非结构化网格的数据结构，
# 包含节点(Node)、边(Link)、面(Face)和体(Body)四个层次。
# 本例创建一个四面体（4个节点、6条边、4个三角形面、1个体），
# 并保存为mesh.xml文件供后续使用。
# 构建步骤为：添加节点→添加边→添加面→添加体。
# 注意：添加面的过程中会自动创建所需的边（Link），因此
# 第二步添加边可以省略，但本例显式执行以展示完整流程。

from zmlx import *


def main():
    """
    创建并保存一个三维四面体网格。

    构建步骤：
    1. 添加4个节点，构成四面体的四个顶点；
    2. 添加6条边，连接所有节点对（此步可省略，添加面时会自动创建边）；
    3. 添加4个三角形面，构成四面体的表面；
    4. 添加1个体，由4个面围成。
    最后将网格保存为mesh.xml文件。

    Returns:
        无返回值。网格保存到mesh.xml文件。
    """
    mesh = Mesh3()  # 创建一个空的Mesh3网格对象

    # 第一步，添加节点（定义四面体的4个顶点坐标）
    mesh.add_node(0, 0, 0)  # 节点0：原点
    mesh.add_node(1, 0, 0)  # 节点1：x轴方向1m处
    mesh.add_node(0, 1, 0)  # 节点2：y轴方向1m处
    mesh.add_node(0, 0, 1)  # 节点3：z轴方向1m处（构成四面体）

    # 第二步，添加边/线（添加面时也会自动创建边，因此这一步可省略）
    mesh.add_link([0, 1])  # 连接节点0和1的边
    mesh.add_link([0, 2])  # 连接节点0和2的边
    mesh.add_link([0, 3])  # 连接节点0和3的边
    mesh.add_link([1, 2])  # 连接节点1和2的边
    mesh.add_link([1, 3])  # 连接节点1和3的边
    mesh.add_link([2, 3])  # 连接节点2和3的边

    # 第三步，添加面（每个面由3条边围成，对应四面体的一个三角形表面）
    mesh.add_face(
        [
            mesh.add_link([1, 2]),  # 面1：由边1-2、2-3、1-3围成
            mesh.add_link([2, 3]),
            mesh.add_link([1, 3]),
        ]
    )
    mesh.add_face(
        [
            mesh.add_link([0, 2]),  # 面2：由边0-2、2-3、0-3围成
            mesh.add_link([2, 3]),
            mesh.add_link([0, 3]),
        ]
    )
    mesh.add_face(
        [
            mesh.add_link([1, 0]),  # 面3：由边1-0、0-3、1-3围成
            mesh.add_link([0, 3]),
            mesh.add_link([1, 3]),
        ]
    )
    mesh.add_face(
        [
            mesh.add_link([1, 2]),  # 面4：由边1-2、2-0、1-0围成
            mesh.add_link([2, 0]),
            mesh.add_link([1, 0]),
        ]
    )

    # 第四步，添加体（由节点0、1、2、3围成的四面体）
    mesh.add_body([0, 1, 2, 3])  # 体由4个节点定义，对应一个四面体

    # 保存网格到XML文件，便于后续读取和使用
    fname = opath("mesh.xml")
    mesh.save(fname)
    print(f"成功，保存到文件：{fname}")


if __name__ == "__main__":
    main()
