"""
定义二氧化碳气液转化临界曲线
参考文献：Span, R.; Wagner, W., A New Equation of State for Carbon Dioxide Covering the Fluid Region from the Triple-Point
Temperature to 1100 K at Pressures up to 800 MPa, J. Phys. Chem. Ref. Data, 1996, 25, 6, 1509-1596, https://doi.org/10.1063/1.555991
"""

from zml import Interp1

if __name__ == '__main__':
    vt = [250, 255, 260, 265, 270, 275, 280, 285, 290, 295, 300]

    vp = [1.7850e6, 2.0843e6, 2.4188e6, 2.7909e6, 3.2033e6, 3.6589e6, 4.1607e6, 4.7123e6, 5.3177e6, 5.9822e6, 6.7131e6]

    t2p = Interp1(x=vt, y=vp).to_evenly_spaced(300)
    p2t = Interp1(x=vp, y=vt).to_evenly_spaced(300)
