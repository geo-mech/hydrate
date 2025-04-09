from zmlx.data.Ye2022.load_txt import load_txt
from zmlx.utility.curve_data import CurveData


def load_curve(name):
    return CurveData(dat=load_txt(name))
