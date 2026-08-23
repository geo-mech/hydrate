"""zmlx GUI 启动入口（``python -m zmlx.ui``）.

Modified by Claude, 2026-08-12
"""

if __name__ == "__main__":
    import sys

    from zmlx.ui.gui_buffer import open_gui

    open_gui(sys.argv)
