"""
尚且处于测试中的模块。在功能稳定之后，会逐步被转移到zml中。因此，这个模块，可以被视为zml模块的一个扩展（会首先导入zml中的所有内容）
"""
from zmlx.exts.base import *

core = DllCore(dll_obj=load_cdll(name='beta.dll', first=os.path.dirname(__file__)))

