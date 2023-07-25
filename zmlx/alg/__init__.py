"""

from zmlx.alg.clamp import clamp
from zmlx.alg.get_frac_width import get_frac_width
from zmlx.alg.has_module import has_module, has_numpy, has_PyQt5, has_scipy, has_matplotlib
from zmlx.filesys.join_paths import join_paths
from zmlx.alg.linspace import linspace
from zmlx.filesys.make_fname import make_fname
from zmlx.alg.mean import mean
from zmlx.filesys.opath import opath
from zmlx.alg.sys import get_latest_version

if has_scipy:
    from zmlx.alg.create_interp1d import create_interp1d
else:
    create_interp1d = None

__all__ = ['clamp', 'get_frac_width', 'join_paths', 'linspace', 'make_fname', 'mean',
           'opath', 'get_latest_version',
           'has_numpy', 'has_PyQt5', 'has_scipy', 'has_matplotlib', 'create_interp1d']



"""
