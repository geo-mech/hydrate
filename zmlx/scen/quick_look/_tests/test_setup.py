"""zml_gui_setup 注册逻辑验证（无 GUI 模式，add_action 为 no-op）."""

from zmlx.scen.quick_look import zml_gui_setup


def main():
    zml_gui_setup.main()
    # main() 内部会导入 _widget，无 GUI 下 add_action 应安全
    print('setup registration OK')


if __name__ == '__main__':
    main()
