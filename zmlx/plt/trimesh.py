import zmlx.alg.sys as warnings
from zmlx.plt.on_ui import show_trimesh as trimesh

warnings.warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)


def test():
    from zmlx.data.trimesh_test import generate_test_mesh
    # 生成测试网格
    triangles, points = generate_test_mesh()
    # 绘制三角形网格
    trimesh(triangles=triangles, points=points, gui_mode=True)


if __name__ == '__main__':
    test()
