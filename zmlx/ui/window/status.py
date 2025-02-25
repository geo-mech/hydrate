def status(*args, **kwargs):
    """
    显示状态信息。参数同status_bar.showMessage函数
    Args:
        *args:
        **kwargs:

    Returns:
        None
    """
    try:
        from zmlx.ui.MainWindow import get_window
        window = get_window()
        if window is not None:
            window.cmd_status(*args, **kwargs)
    except:
        pass
