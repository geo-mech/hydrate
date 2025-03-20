import random

from zml import LinearExpr, Seepage


def show_cell(cell: Seepage.CellData):
    print(cell.fluid_number, cell.pre, cell.get_attr(0), end='\t')
    for i in range(cell.fluid_number):
        print(cell.get_fluid(i).vol, end='\t')
    print()


def main():
    model = Seepage()
    model.add_cell()
    model.add_cell()
    for c in model.cells:
        assert isinstance(c, Seepage.Cell)
        c.fluid_number = 2
        c.set_pore(1, 1.001, 1, 1)
        for i in range(c.fluid_number):
            c.get_fluid(i).vol = random.uniform(0, 2)
        c.set_attr(0, random.uniform(0, 2))
    model.get_cell(0).fluid_number = 1  # 故意删除一个流体

    lexpr = LinearExpr()

    lexpr.add(0, 0.1)
    lexpr.add(1, 0.9)

    cell = Seepage.CellData()
    cell.set_fluids_by_lexpr(lexpr, model)
    cell.set_pore_by_lexpr(lexpr, model)
    cell.set_density_attr_by_lexpr(0, lexpr, model)

    show_cell(model.get_cell(0))
    show_cell(model.get_cell(1))
    show_cell(cell)


if __name__ == '__main__':
    main()
