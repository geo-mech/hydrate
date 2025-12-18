from zmlx import *
from zmlx.fluid.nist.ch4 import create


def main():
    flu = create(name='ch4')
    filename = app_data.temp('ch4.xml')
    flu.save(filename)
    gui.open_fludef(filename)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
