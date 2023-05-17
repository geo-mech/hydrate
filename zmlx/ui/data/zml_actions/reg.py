# ** is_sys = True
# ** text = '注册'

from zml import *

text = f"""请发送以下内容给作者(zhangzhaobin@mail.iggcas.ac.cn): 
   1. 姓名、单位及联系方式;
   2. 本机识别码: 
<{reg()}>. 
感谢使用!
"""
print(text)
gui.about('提示', text)
