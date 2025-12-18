from zmlx import *
from zmlx.fluid.nist.co2 import create


def main():
    flu = create(name='co2')
    filename = app_data.temp('co2.xml')
    flu.save(filename)
    gui.open_fludef(filename)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
