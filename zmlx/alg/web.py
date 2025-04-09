"""
网页相关的操作。直接从webbrowser导入即可
"""
from webbrowser import open_new_tab, open, open_new

__all__ = ['open_new_tab', 'open', 'open_new']

import zmlx.alg.sys as warnings

warnings.warn("zmlx.alg.web is deprecated "
              "(will be removed after 2026-5-16), "
              "please use webbrowser instead",
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    open_new_tab('https://gitee.com/geomech/hydrate')
