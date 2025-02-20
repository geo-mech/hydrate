from zml import SeepageMesh


def load_ascii(cellfile, facefile, mesh=None):
    """
    从文件中导入几何结构。其中cellfile定义cell的信息，至少包含4列，分别为x,y,z,vol；
    facefile定义face的性质，至少包含4裂缝，分别为cell_i0,cell_i1,area,length
    """
    if mesh is None:
        mesh = SeepageMesh()

    mesh.clear()
    with open(cellfile, 'r') as file:
        for line in file.readlines():
            vals = [float(s) for s in line.split()]
            if len(vals) == 0:
                continue
            assert len(vals) >= 4
            cell = mesh.add_cell()
            assert cell is not None
            cell.pos = [vals[i] for i in range(0, 3)]
            cell.vol = vals[3]
    cell_number = mesh.cell_number
    with open(facefile, 'r') as file:
        for line in file.readlines():
            words = line.split()
            if len(words) == 0:
                continue
            assert len(words) >= 4
            cell_i0 = int(words[0])
            cell_i1 = int(words[1])
            assert cell_i0 < cell_number
            assert cell_i0 < cell_number
            area = float(words[2])
            assert area > 0
            length = float(words[3])
            assert length > 0
            face = mesh.add_face(mesh.get_cell(cell_i0), mesh.get_cell(cell_i1))
            if face is not None:
                face.area = area
                face.length = length
    # 返回导入的mesh
    return mesh


def save_ascii(cellfile, facefile, mesh):
    """
    将当前的网格数据导出到两个文件
    """
    with open(cellfile, 'w') as file:
        for cell in mesh.cells:
            for elem in cell.pos:
                file.write('%g ' % elem)
            file.write('%g\n' % cell.vol)
    with open(facefile, 'w') as file:
        for face in mesh.faces:
            link = face.link
            file.write('%d %d %g %g\n' % (link[0], link[1],
                                          face.area, face.length))
