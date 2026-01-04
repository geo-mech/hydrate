from zmlx.exts import SelfPath
from zmlx.fluid.alg import from_data, from_file
from zmlx.fluid.alg import load_fludefs
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.ch4_hydrate import create as create_ch4_hydrate
from zmlx.fluid.co2 import create as create_co2
from zmlx.fluid.co2_hydrate import create as create_co2_hydrate
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.h2o_gas import create as create_h2o_gas
from zmlx.fluid.h2o_ice import create as create_h2o_ice

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
