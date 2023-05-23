from zml import *


def try_open(model):
    assert isinstance(model, Seepage)
    ca_open = model.reg_cell_key('is_open')
    count = 0
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        is_open = cell.get_attr(ca_open)
        if abs(is_open) < 0.5:
            if cell.pre > 1.5e6:
                cell.v0 *= 2
                cell.set_attr(ca_open, 1)
                count += 1
    return count
