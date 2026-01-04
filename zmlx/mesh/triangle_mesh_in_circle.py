"""
对于坐标在0, 0，半径为r的一个圆。现在，我要在其中划分三角形网格，给定网格边长目标值为l
(实际的三角形为随机的，允许长度大约在0.7l到1.3l之间变化)，请帮我写一个Python函数，
返回triangles(从0开始的节点编号，3个编号定义一个三角形)和平面内顶点的坐标vertexes。
注意，随着内部的三角形是随机的，但是对于园的边缘，还是要清晰地刻画出来。后续，我需要用这个三角新网格，来进行渗流或者有限元计算。


在生成随机点的时候，请检查和当前已有点的距离，如果距离小于某一个阈值，则抛弃这个随机点。
我看了你生成的三角形网格，在边界附近，我感觉某些点之家的距离有些过小了。
"""
import time
from typing import Tuple, Optional

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Delaunay, KDTree


def generate_circle_mesh_improved(r: float, l: float, center: Tuple[float, float] = (0, 0),
                                  min_ratio: float = 0.7, max_ratio: float = 1.3,
                                  use_kdtree: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    改进版：在圆形区域内生成三角形网格，避免点之间距离过小

    Args:
        r: 圆的半径
        l: 目标网格边长
        center: 圆心坐标 (cx, cy)，默认为(0, 0)
        min_ratio: 最小边长比例（相对于l）
        max_ratio: 最大边长比例（相对于l）
        use_kdtree: 是否使用KDTree加速距离查询

    Returns:
        vertexes: 顶点坐标数组，形状为 (n_vertices, 2)
        triangles: 三角形索引数组，形状为 (n_triangles, 3)
    """
    cx, cy = center

    # 1. 生成边界点
    circumference = 2 * np.pi * r
    n_boundary = max(8, int(circumference / l))

    # 生成边界点，确保边界点之间距离均匀
    theta = np.linspace(0, 2 * np.pi, n_boundary, endpoint=False)
    boundary_points = np.column_stack([
        cx + r * np.cos(theta),
        cy + r * np.sin(theta)
    ])

    # 计算边界点之间的平均距离
    boundary_distances = []
    for i in range(n_boundary):
        p1 = boundary_points[i]
        p2 = boundary_points[(i + 1) % n_boundary]
        boundary_distances.append(np.linalg.norm(p1 - p2))

    avg_boundary_dist = np.mean(boundary_distances)
    print(f"边界点数量: {n_boundary}, 平均边界点间距: {avg_boundary_dist:.3f}")

    # 2. 在圆内部生成随机点，避免距离过近
    min_distance = min_ratio * l  # 最小允许距离
    internal_points = []
    all_points_so_far = boundary_points.copy()  # 包含所有已有点的列表

    # 计算可以生成的内部点数量估计
    area = np.pi * r ** 2
    # 每个点占据的面积大约为等边三角形面积
    point_area = (np.sqrt(3) / 4) * l ** 2
    max_internal_points = int(area / point_area) + 10

    if use_kdtree:
        # 使用KDTree加速距离查询
        tree = KDTree(all_points_so_far)

    attempts = 0
    max_attempts = max_internal_points * 20  # 最大尝试次数

    while len(internal_points) < max_internal_points and attempts < max_attempts:
        attempts += 1

        # 生成随机点
        # 在圆内均匀采样
        # 方法1: 在方形区域内采样，然后判断是否在圆内
        x = np.random.uniform(cx - r, cx + r)
        y = np.random.uniform(cy - r, cy + r)

        # 检查点是否在圆内
        if (x - cx) ** 2 + (y - cy) ** 2 > r ** 2:
            continue

        # 检查与已有点的距离
        point = np.array([x, y])

        if use_kdtree:
            # 使用KDTree查询最近邻
            dist, idx = tree.query(point, k=1)
            if dist < min_distance:
                continue
        else:
            # 直接计算与所有点的距离
            distances = np.sqrt(np.sum((all_points_so_far - point) ** 2, axis=1))
            min_dist = np.min(distances)
            if min_dist < min_distance:
                continue

        # 点被接受
        internal_points.append(point)
        all_points_so_far = np.vstack([all_points_so_far, [point]])

        if use_kdtree:
            # 更新KDTree
            tree = KDTree(all_points_so_far)

    if internal_points:
        internal_points_array = np.array(internal_points)
        all_points = np.vstack([boundary_points, internal_points_array])
    else:
        all_points = boundary_points

    print(f"生成了 {len(internal_points)} 个内部点，尝试次数: {attempts}")

    # 3. 可选：对内部点进行Lloyd松弛，使点分布更均匀
    if len(internal_points) > 0:
        all_points = lloyd_relaxation(all_points, boundary_points, cx, cy, r, iterations=3)

    # 4. 进行Delaunay三角剖分
    tri = Delaunay(all_points)

    # 5. 过滤掉在圆外的三角形
    triangles = []
    for simplex in tri.simplices:
        # 计算三角形重心
        A = all_points[simplex[0]]
        B = all_points[simplex[1]]
        C = all_points[simplex[2]]

        center_x = (A[0] + B[0] + C[0]) / 3
        center_y = (A[1] + B[1] + C[1]) / 3

        # 检查重心是否在圆内
        if (center_x - cx) ** 2 + (center_y - cy) ** 2 <= r ** 2:
            triangles.append(simplex)

    triangles = np.array(triangles)

    return all_points, triangles


def lloyd_relaxation(points: np.ndarray, boundary_points: np.ndarray,
                     cx: float, cy: float, r: float, iterations: int = 3) -> np.ndarray:
    """
    Lloyd松弛算法，使点分布更均匀

    Args:
        points: 所有点的坐标
        boundary_points: 边界点（不移动）
        cx, cy, r: 圆心和半径
        iterations: 迭代次数

    Returns:
        松弛后的点坐标
    """
    from scipy.spatial import Voronoi

    if len(points) <= len(boundary_points):
        return points

    # 标记边界点
    n_boundary = len(boundary_points)
    boundary_indices = set(range(n_boundary))

    for iter_num in range(iterations):
        # 计算Voronoi图
        vor = Voronoi(points)

        # 创建新点列表
        new_points = np.copy(points)

        # 更新每个内部点的位置为其Voronoi单元的重心
        for i in range(len(points)):
            if i in boundary_indices:
                # 边界点不移动
                continue

            # 获取该点的Voronoi区域
            region_idx = vor.point_region[i]
            region = vor.regions[region_idx]

            if -1 in region or len(region) == 0:
                # 无效区域，跳过
                continue

            # 获取区域顶点
            region_vertices = vor.vertices[region]

            # 计算重心
            if len(region_vertices) > 0:
                # 计算多边形重心
                centroid = np.mean(region_vertices, axis=0)

                # 确保重心在圆内
                if (centroid[0] - cx) ** 2 + (centroid[1] - cy) ** 2 <= r ** 2:
                    new_points[i] = centroid

        points = new_points

    return points


def generate_circle_mesh_hexagonal(r: float, l: float, center: Tuple[float, float] = (0, 0)) -> Tuple[
    np.ndarray, np.ndarray]:
    """
    使用六边形网格生成圆形区域的三角形网格
    这种方法生成的点分布更均匀

    Args:
        r: 圆的半径
        l: 目标网格边长
        center: 圆心坐标 (cx, cy)

    Returns:
        vertexes: 顶点坐标数组
        triangles: 三角形索引数组
    """
    cx, cy = center

    # 生成六边形网格点
    # 六边形网格的间距
    dx = l
    dy = l * np.sqrt(3) / 2

    # 计算网格范围
    n_x = int(2 * r / dx) + 2
    n_y = int(2 * r / dy) + 2

    points = []

    for i in range(-n_x, n_x + 1):
        for j in range(-n_y, n_y + 1):
            # 六边形网格偏移
            if j % 2 == 0:
                x = cx + i * dx
            else:
                x = cx + (i + 0.5) * dx

            y = cy + j * dy

            # 检查点是否在圆内
            if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                points.append([x, y])

    # 添加边界点
    circumference = 2 * np.pi * r
    n_boundary = max(8, int(circumference / l))
    theta = np.linspace(0, 2 * np.pi, n_boundary, endpoint=False)
    boundary_points = np.column_stack([
        cx + r * np.cos(theta),
        cy + r * np.sin(theta)
    ])

    # 合并点
    all_points = np.vstack([points, boundary_points])

    # 进行Delaunay三角剖分
    tri = Delaunay(all_points)

    # 过滤掉在圆外的三角形
    triangles = []
    for simplex in tri.simplices:
        A = all_points[simplex[0]]
        B = all_points[simplex[1]]
        C = all_points[simplex[2]]

        center_x = (A[0] + B[0] + C[0]) / 3
        center_y = (A[1] + B[1] + C[1]) / 3

        if (center_x - cx) ** 2 + (center_y - cy) ** 2 <= r ** 2:
            triangles.append(simplex)

    triangles = np.array(triangles)

    return all_points, triangles


def analyze_mesh_quality(vertexes: np.ndarray, triangles: np.ndarray) -> dict:
    """
    分析网格质量

    Args:
        vertexes: 顶点坐标
        triangles: 三角形索引

    Returns:
        包含各种质量指标的字典
    """
    edge_lengths = []
    aspect_ratios = []
    min_angles = []
    max_angles = []
    areas = []

    for triangle in triangles:
        A, B, C = triangle
        p1, p2, p3 = vertexes[A], vertexes[B], vertexes[C]

        # 计算边长
        a = np.linalg.norm(p2 - p3)  # 对边A
        b = np.linalg.norm(p1 - p3)  # 对边B
        c = np.linalg.norm(p1 - p2)  # 对边C

        edge_lengths.extend([a, b, c])

        # 计算角度
        # 使用余弦定理
        if a > 0 and b > 0 and c > 0:
            angle_A = np.degrees(np.arccos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)))
            angle_B = np.degrees(np.arccos((a ** 2 + c ** 2 - b ** 2) / (2 * a * c)))
            angle_C = 180 - angle_A - angle_B

            angles = [angle_A, angle_B, angle_C]
            min_angles.append(min(angles))
            max_angles.append(max(angles))

            # 计算长宽比（最长边/最短边）
            aspect_ratio = max([a, b, c]) / min([a, b, c])
            aspect_ratios.append(aspect_ratio)

        # 计算面积（海伦公式）
        s = (a + b + c) / 2
        area = np.sqrt(max(0, s * (s - a) * (s - b) * (s - c)))  # 避免负数
        areas.append(area)

    edge_lengths = np.array(edge_lengths)
    aspect_ratios = np.array(aspect_ratios)
    min_angles = np.array(min_angles)
    max_angles = np.array(max_angles)
    areas = np.array(areas)

    stats = {
        'vertex_count': len(vertexes),
        'triangle_count': len(triangles),
        'edge_length': {
            'mean': np.mean(edge_lengths),
            'min': np.min(edge_lengths),
            'max': np.max(edge_lengths),
            'std': np.std(edge_lengths)
        },
        'aspect_ratio': {
            'mean': np.mean(aspect_ratios),
            'min': np.min(aspect_ratios),
            'max': np.max(aspect_ratios)
        },
        'angle': {
            'min_mean': np.mean(min_angles),
            'min_min': np.min(min_angles),
            'max_mean': np.mean(max_angles),
            'max_max': np.max(max_angles)
        },
        'area': {
            'mean': np.mean(areas),
            'min': np.min(areas),
            'max': np.max(areas)
        }
    }

    return stats


def plot_mesh_with_quality(vertexes: np.ndarray, triangles: np.ndarray,
                           r: float, center: Tuple[float, float] = (0, 0),
                           stats: Optional[dict] = None):
    """绘制生成的三角形网格并显示质量信息"""
    fig, axes = plt.subplots(1, 2)

    # 左图：绘制网格
    ax1 = axes[0]
    ax1.triplot(vertexes[:, 0], vertexes[:, 1], triangles, 'b-', linewidth=0.5, alpha=0.7)
    ax1.plot(vertexes[:, 0], vertexes[:, 1], 'ro', markersize=2)

    # 绘制圆形边界
    circle = plt.Circle(center, r, color='black', fill=False, linewidth=2)
    ax1.add_patch(circle)

    ax1.set_aspect('equal')
    ax1.set_xlim(center[0] - r * 1.1, center[0] + r * 1.1)
    ax1.set_ylim(center[1] - r * 1.1, center[1] + r * 1.1)
    ax1.set_title(f"圆形网格 (半径={r}, 顶点数={len(vertexes)}, 三角形数={len(triangles)})")
    ax1.grid(True, alpha=0.3)

    # 右图：绘制边长分布
    if stats is not None:
        ax2 = axes[1]

        # 计算边长用于直方图
        edge_lengths = []
        for triangle in triangles:
            A, B, C = triangle
            p1, p2, p3 = vertexes[A], vertexes[B], vertexes[C]
            edge_lengths.extend([
                np.linalg.norm(p1 - p2),
                np.linalg.norm(p2 - p3),
                np.linalg.norm(p3 - p1)
            ])

        ax2.hist(edge_lengths, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.axvline(x=stats['edge_length']['mean'], color='red', linestyle='--',
                    label=f"均值: {stats['edge_length']['mean']:.3f}")
        ax2.axvline(x=stats['edge_length']['min'], color='green', linestyle='--',
                    label=f"最小值: {stats['edge_length']['min']:.3f}")
        ax2.axvline(x=stats['edge_length']['max'], color='orange', linestyle='--',
                    label=f"最大值: {stats['edge_length']['max']:.3f}")

        ax2.set_xlabel('边长')
        ax2.set_ylabel('频数')
        ax2.set_title('边长分布直方图')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def generate_mesh_quality_report(vertexes: np.ndarray, triangles: np.ndarray,
                                 target_length: float, min_ratio: float, max_ratio: float):
    """生成网格质量报告"""
    stats = analyze_mesh_quality(vertexes, triangles)

    print("=" * 60)
    print("网格质量分析报告")
    print("=" * 60)
    print(f"顶点数: {stats['vertex_count']}")
    print(f"三角形数: {stats['triangle_count']}")
    print(f"边数: {3 * stats['triangle_count'] // 2} (约)")

    print("\n边长统计:")
    print(f"  平均值: {stats['edge_length']['mean']:.3f}")
    print(f"  最小值: {stats['edge_length']['min']:.3f}")
    print(f"  最大值: {stats['edge_length']['max']:.3f}")
    print(f"  标准差: {stats['edge_length']['std']:.3f}")

    # 检查边长是否在目标范围内
    target_min = min_ratio * target_length
    target_max = max_ratio * target_length
    edges_in_range = np.sum((stats['edge_length']['min'] >= target_min * 0.9) &
                            (stats['edge_length']['max'] <= target_max * 1.1))
    print(f"\n边长目标范围: [{target_min:.3f}, {target_max:.3f}]")

    print("\n三角形质量:")
    print(f"  最小角平均值: {stats['angle']['min_mean']:.1f}°")
    print(f"  最小角最小值: {stats['angle']['min_min']:.1f}°")
    print(f"  最大角平均值: {stats['angle']['max_mean']:.1f}°")
    print(f"  最大角最大值: {stats['angle']['max_max']:.1f}°")

    # 质量评估
    print("\n质量评估:")
    if stats['angle']['min_min'] < 20:
        print("  ⚠️  警告: 存在过小的角（<20°），可能导致数值计算问题")
    else:
        print("  ✓ 最小角正常")

    if stats['aspect_ratio']['max'] > 3:
        print("  ⚠️  警告: 存在高长宽比的三角形（>3），可能导致数值不稳定")
    else:
        print("  ✓ 三角形形状良好")

    if stats['edge_length']['std'] / stats['edge_length']['mean'] > 0.5:
        print("  ⚠️  警告: 边长变化较大，建议调整网格参数")
    else:
        print("  ✓ 边长分布均匀")

    print("=" * 60)

    return stats


def test():
    # 参数设置
    radius = 5.0
    target_length = 0.5
    center_point = (0, 0)
    min_ratio = 0.7
    max_ratio = 1.3

    print("正在生成圆形网格...")
    print(f"半径: {radius}")
    print(f"目标边长: {target_length}")
    print(f"圆心: {center_point}")
    print(f"边长范围: [{min_ratio * target_length:.3f}, {max_ratio * target_length:.3f}]")

    # 生成网格
    start_time = time.time()
    vertexes, triangles = generate_circle_mesh_improved(
        r=radius,
        l=target_length,
        center=center_point,
        min_ratio=min_ratio,
        max_ratio=max_ratio,
        use_kdtree=True
    )
    end_time = time.time()

    print(f"\n网格生成完成，耗时: {end_time - start_time:.2f}秒")

    # 分析网格质量
    stats = generate_mesh_quality_report(vertexes, triangles, target_length, min_ratio, max_ratio)

    # 绘制网格
    plot_mesh_with_quality(vertexes, triangles, radius, center_point, stats)

    # # 可选：保存网格
    # # np.savez("circle_mesh.npz", vertexes=vertexes, triangles=triangles)
    #
    # # 可选：尝试六边形网格
    # print("\n尝试生成六边形网格...")
    # vertexes_hex, triangles_hex = generate_circle_mesh_hexagonal(radius, target_length, center_point)
    # stats_hex = generate_mesh_quality_report(vertexes_hex, triangles_hex, target_length, min_ratio, max_ratio)
    # plot_mesh_with_quality(vertexes_hex, triangles_hex, radius, center_point, stats_hex)


# 主函数
if __name__ == "__main__":
    test()
