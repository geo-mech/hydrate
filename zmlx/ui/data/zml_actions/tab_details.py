text = '标签列表'
tooltip = '在一个标签页内显示所有标签也的摘要，当标签特别多的时候比较有用'
menu = '帮助'


def slot():
    from zmlx.ui.MainWindow import get_window
    window = get_window()
    if window is not None:
        window.tab_details()
