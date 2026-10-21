# ** desc = 'pyqtgraph ParameterTree 示例：用纯字典声明参数树，自动生成 float/bool/list/str/action 等交互控件'
# ** highlight = '#8c510a'

from zmlx import *


def main():
    def setup(tree):
        from pyqtgraph.parametertree import Parameter
        params = [
            {'name': 'Grid', 'type': 'group', 'children': [
                {'name': 'nx', 'type': 'int', 'value': 50, 'limits': [1, 500]},
                {'name': 'nz', 'type': 'int', 'value': 50, 'limits': [1, 500]},
                {'name': 'Length / m', 'type': 'float', 'value': 100, 'limits': [1, None], 'step': 10},
            ]},
            {'name': 'Physics', 'type': 'group', 'children': [
                {'name': 'Permeability / mD', 'type': 'float', 'value': 100,
                 'limits': [0.001, 10000], 'step': 10, 'siPrefix': True},
                {'name': 'Porosity', 'type': 'float', 'value': 0.2, 'limits': [0.01, 0.5], 'step': 0.01},
                {'name': 'Gravity enabled', 'type': 'bool', 'value': True},
                {'name': 'Fluid', 'type': 'list', 'limits': ['H2O', 'CH4', 'CO2']},
            ]},
            {'name': 'Solver', 'type': 'group', 'children': [
                {'name': 'Max time / years', 'type': 'float', 'value': 10,
                 'limits': [0.1, 1000], 'step': 1, 'suffix': 'yr'},
                {'name': 'CFL', 'type': 'float', 'value': 0.1,
                 'limits': [0.01, 1.0], 'step': 0.01},
                {'name': 'Output interval / days', 'type': 'int', 'value': 30,
                 'limits': [1, 365]},
            ]},
            {'name': '显示参数', 'type': 'action'},
        ]

        p = Parameter.create(name='root', type='group', children=params)
        p.param('显示参数').sigActivated.connect(lambda: print(p.saveState()))
        tree.setParameters(p, showTop=False)

    from pyqtgraph.parametertree import ParameterTree

    gui.get_widget(the_type=ParameterTree, caption='ParameterTree 示例', init=setup)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
