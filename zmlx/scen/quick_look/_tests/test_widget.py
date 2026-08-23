"""QuickLookWidget 无头测试：控件构建 + 参数解析 + evaluate 调用 + 绘图."""

import os

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from zmlx.ui.pyqt import QtWidgets
from zmlx.scen.quick_look._widget import (QuickLookWidget, parse_tuple,
                                          parse_control_p, parse_frac_segs)

app = QtWidgets.QApplication([])  # 单一 QApplication，供所有测试复用


def test_parse():
    assert parse_tuple('0, 400') == (0.0, 400.0)
    assert parse_tuple('(0, 400)') == (0.0, 400.0)
    assert parse_control_p('(0,0);(100,200)') == [(0.0, 0.0), (100.0, 200.0)]
    assert parse_control_p('') is None
    segs = parse_frac_segs('(0,200)-(400,200)-5')
    assert segs == [((0.0, 200.0), (400.0, 200.0), 5.0)], segs
    assert parse_frac_segs('') is None
    print('parse functions OK')


def test_widget():
    w = QuickLookWidget()
    print('widget created OK')

    # 默认值填充
    assert float(w._param_widgets['p'].get_text()) == 1e6
    assert w._param_widgets['x_range'].text() == '0, 400'
    assert w._param_widgets['dx'].text() == '10.0'
    assert w._param_widgets['dy'].text() == ''

    # 表单读取（标量）
    w._param_widgets['control_p'].setText('(0,0);(400,400)')
    w._param_widgets['frac_segs'].setText('(0,200)-(400,200)-5')
    params = w._get_params()
    assert params['dx'] == 10.0
    assert params['dy'] is None
    assert params['control_p'] == [(0.0, 0.0), (400.0, 400.0)]
    assert params['frac_segs'] == [((0.0, 200.0), (400.0, 200.0), 5.0)]
    assert params['x_range'] == (0.0, 400.0)
    assert params['p'] == 1e6
    assert params['step_max'] == 100

    # 表单读取（函数定义）
    w._param_widgets['p'].setText(
        'def p(x, y, z):\n'
        '    return 15e6 if x < 50 else 5e6\n')
    params = w._get_params()
    assert callable(params['p'])
    assert params['p'](0, 0, 0) == 15e6
    assert params['p'](100, 100, 0) == 5e6

    # 缺 p 定义 → 报错
    w._param_widgets['p'].setText('x = 1')
    try:
        w._get_params()
        assert False, '应抛出 ValueError'
    except ValueError:
        pass
    print('param gathering OK')


def test_e2e():
    """完整链路：表单 → evaluate → 绘图（压力场函数）."""
    w = QuickLookWidget()
    w._param_widgets['control_p'].setText('(0,0);(400,400)')
    w._param_widgets['frac_segs'].setText('(0,200)-(400,200)-5')
    w._param_widgets['p'].setText(
        'def p(x, y, z):\n'
        '    return 15e6 if x < 50 else 5e6\n')
    params = w._get_params()
    from zmlx.scen.quick_look import evaluate
    r = evaluate(**params)
    assert len(r['p']) > 0
    assert r['n_step'] >= 1
    # 压力场应呈现两侧分布（左侧 15 MPa 区域压力更高）
    assert r['p'].max() > 1e6
    print(f'evaluate OK: n_step={r["n_step"]}, n_cell={len(r["p"])}, '
          f'p range: {r["p"].min() * 1e-6:.2f}–{r["p"].max() * 1e-6:.2f} MPa')

    # 绘制到控件内嵌 figure
    w._show_result(r)
    fig = w._plot.figure
    fig.savefig('test_widget_e2e.png', dpi=80)
    print('plot OK')


if __name__ == '__main__':
    test_parse()
    test_widget()
    test_e2e()
    print('ALL TESTS PASSED')
