"""
网页相关的操作。直接从webbrowser导入即可
.

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from webbrowser import open_new_tab, open, open_new

__all__ = ['open_new_tab', 'open', 'open_new']


warn("zmlx.alg.web is deprecated "
              "(will be removed after 2026-5-16), "
              "please use webbrowser instead",
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    open_new_tab('https://gitee.com/geomech/hydrate')
