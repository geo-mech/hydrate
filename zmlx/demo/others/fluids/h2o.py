from zmlx import *
from zmlx.fluid.nist.h2o import create


def main():
    flu = create(name='h2o')
    filename = app_data.temp('h2o.xml')
    flu.save(filename)
    gui.open_fludef(filename)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
