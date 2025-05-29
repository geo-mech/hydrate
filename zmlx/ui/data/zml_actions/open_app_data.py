text = '打开AppData目录'
menu = '帮助'


def slot():
    from zml import app_data
    import os
    os.startfile(app_data.root())


def enabled():
    from zml import lic
    return lic.is_admin
