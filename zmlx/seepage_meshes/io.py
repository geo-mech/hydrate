"""渗流网格 IO（ASCII 格式读写）。

Modified by Claude, 2026-08-12
"""
from zmlx.exts import SeepageMesh


def load_ascii(cell_file, face_file, mesh=None):
    """
    从文件中导入几何结构。其中cell_file定义cell的信息，至少包含4列，分别为x,y,z,vol；
    face_file定义face的性质，至少包含4裂缝，分别为cell_i0,cell_i1,area,length
    """
    if mesh is None:
        mesh = SeepageMesh()

    mesh.clear()
    with open(cell_file, 'r') as file:
        for line in file.readlines():
            words = line.split()
            if len(words) == 0:  # 空行（含文件末尾的换行）跳过
                continue
            # ⚠️ 必须先判空再转 float：原先把 vals 的推导写在判空之前，
            #    line.split() 为空时 float() 已经抛 ValueError 了，那句
            #    `if len(vals) == 0: continue` 是永远到不了的死代码 ——
            #    于是「文件末尾有一个空行」这种最常见的输入直接崩。
            vals = [float(s) for s in words]
            assert len(vals) >= 4
            cell = mesh.add_cell()
            assert cell is not None
            cell.pos = [vals[i] for i in range(0, 3)]
            cell.vol = vals[3]
    cell_number = mesh.cell_number
    with open(face_file, 'r') as file:
        for line in file.readlines():
            words = line.split()
            if len(words) == 0:
                continue
            assert len(words) >= 4
            cell_i0 = int(words[0])
            cell_i1 = int(words[1])
            # ⚠️ 两个 cell 索引**都要**校验，且都要查**下界**。
            #    原先把第一行复制了一遍（两行都是 cell_i0），cell_i1 从未被
            #    检查；而只写 `< cell_number` 又拦不住负数索引（int('-1') 能过
            #    断言，随后 get_cell(-1) 返回 None，add_face 会抛出难懂的
            #    ctypes ArgumentError）。
            assert 0 <= cell_i0 < cell_number
            assert 0 <= cell_i1 < cell_number
            area = float(words[2])
            assert area > 0
            length = float(words[3])
            assert length > 0
            face = mesh.add_face(
                mesh.get_cell(cell_i0), mesh.get_cell(cell_i1))
            if face is not None:
                face.area = area
                face.length = length
    # 返回导入的mesh
    return mesh


def save_ascii(cell_file, face_file, mesh):
    """
    将当前的网格数据导出到两个文件
    """
    with open(cell_file, 'w') as file:
        for cell in mesh.cells:
            for elem in cell.pos:
                file.write('%g ' % elem)
            file.write('%g\n' % cell.vol)
    with open(face_file, 'w') as file:
        for face in mesh.faces:
            link = face.link
            file.write('%d %d %g %g\n' % (
                link[0], link[1], face.area, face.length))


def load_mesh(cell_file=None, face_file=None, path=None):
    """
    从文件中读取Mesh文件
    """
    mesh = SeepageMesh()
    if path is not None:
        assert cell_file is None and face_file is None
        mesh.load(path)
    else:
        assert cell_file is not None and face_file is not None
        load_ascii(cell_file, face_file, mesh=mesh)
    return mesh
