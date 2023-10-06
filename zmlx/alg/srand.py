from zml import *
import random


def srand(seed):
    """
    设置Python和zml内核的随机数种子.  2023-9-25
    """
    random.seed(seed)
    set_srand(seed)
