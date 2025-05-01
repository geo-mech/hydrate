text = '创建桌面快捷方式'
menu = '帮助'


def slot():
    from zmlx.alg.sys import create_ui_lnk_on_desktop
    create_ui_lnk_on_desktop()
