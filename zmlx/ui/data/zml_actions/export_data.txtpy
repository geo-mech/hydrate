# ** text = '导出'
# ** menu = '文件'
# ** name = 'action_export_data'

from zml import app_data

main_window = app_data.space.get('main_window', None)
if main_window is not None:
    widget = main_window.tab_widget.currentWidget()
    if hasattr(widget, 'export_data'):
        main_window.task_proc.add(lambda: widget.export_data())
