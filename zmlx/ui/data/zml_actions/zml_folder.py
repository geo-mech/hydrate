text = '数据文件夹'
menu = '帮助'


def slot():
    from zml import app_data
    import os
    os.startfile(app_data.root())
