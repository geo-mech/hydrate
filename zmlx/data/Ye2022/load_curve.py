from zmlx.data.Ye2022.load_txt import load_txt
from zmlx.utility.CurveData import CurveData


def load_curve(name):
    return CurveData(dat=load_txt(name))
