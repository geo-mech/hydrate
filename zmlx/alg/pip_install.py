import subprocess

from zml import app_data
from zmlx.alg.has_module import has_module


def pip_install(name):
    if not has_module(name):
        path = app_data.find(name='python.exe')
        rc, out = subprocess.getstatusoutput(f'{path} -m pip install {name}')
        print(out)
