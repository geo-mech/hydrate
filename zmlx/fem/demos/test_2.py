from zmlx.fem.xy import FemModel, Mesh3, LinkType


def create_mesh():
    """
    创建mesh，供测试
    """
    mesh: Mesh3 = Mesh3()

    # 添加node
    nodes = [mesh.add_node(*pos) for pos in
             [(0, 0, 0), (1, 0, 0), (0.5, 1, 0), (1.5, 1, 0), (1, 2, 0), (2, 2, 0)]
             ]

    # 添加link和face
    for triangle in [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5)]:
        n0 = nodes[triangle[0]]
        n1 = nodes[triangle[1]]
        n2 = nodes[triangle[2]]
        mesh.add_face(
            [mesh.add_link([n0, n1]), mesh.add_link([n1, n2]),
             mesh.add_link([n2, n0])]
        )
    return mesh


def _create(mesh: Mesh3):
    """
    根据mesh创建模型
    """
    model = FemModel()

    model.set_mesh(
        mesh,
        face_density=[1.0] * mesh.face_number,
        face_thickness=[1] * mesh.face_number,
        link_types=[LinkType.Truss2] * mesh.link_number,
        link_area=[1.0] * mesh.link_number,
        link_ym=[1.0] * mesh.link_number,
    )

    # 增大质量，以确保位置不变
    model.set_mass(node_id=0, dim=0, value=1e20)
    model.set_mass(node_id=0, dim=1, value=1e20)
    model.set_mass(node_id=1, dim=1, value=1e20)

    # 修改初始位置，打破平衡状态
    model.set_disp(node_id=5, dim=0, value=0.2)
    return model


def _show(model: FemModel):
    """
    绘图
    """
    from zmlx.plt import add_tricontourf, plot_on_figure
    dx, dy = model.get_disp()
    vx, vy = model.get_pos()
    vx += dx
    vy += dy

    def on_figure(figure):
        from zmlx.plt import AutoLayout
        layout = AutoLayout(figure, num_plots=2, subplot_aspect_ratio=1.5, xlabel='x', ylabel='y', aspect='equal')
        ax = layout.add_axes2(title='displacement x')
        add_tricontourf(ax, vx, vy, dx, cbar={'label': 'dx'})
        ax = layout.add_axes2(title='displacement y')
        add_tricontourf(ax, vx, vy, dy, cbar={'label': 'dy'})
        figure.tight_layout()

    plot_on_figure(on_figure, caption='displacement')


def _solve(model: FemModel):
    """
    求解给定的模型
    """
    from zmlx import gui
    for step in range(500):
        gui.break_point()
        print(f'step = {step}')
        model.iterate(dt=0.1)
        if step % 5 == 0:
            _show(model)


def _test(gui_mode=True, close_after_done=False):
    """
    主函数
    """
    from zmlx import gui
    mesh = create_mesh()
    model = _create(mesh=mesh)
    gui.execute(func=_solve, args=[model],
                close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    _test()
