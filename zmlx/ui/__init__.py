# -*- coding: utf-8 -*-

from zmlx.alg.has_module import has_PyQt5

if has_PyQt5:
    from zmlx.ui.MainWindow import execute
    from zmlx.ui.Matplot import *
    from zmlx.ui.Config import find, find_all
    from zmlx.ui.CodeAlg import *
