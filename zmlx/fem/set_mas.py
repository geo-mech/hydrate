import warnings

warnings.warn(f"{__file__} is deprecated", DeprecationWarning, stacklevel=2)
from zmlx.fem.set_mass import set_mass

set_mas = set_mass
