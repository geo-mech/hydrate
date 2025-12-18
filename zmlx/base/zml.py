import os

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-12-19',
              DeprecationWarning, stacklevel=2)

fname = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__))),
    'zml.py'
)
if os.path.isfile(fname):
    with open(fname, 'r', encoding='utf-8') as f:
        code = f.read()
        # 执行代码，将其内容添加到当前命名空间
        exec(code, globals())
