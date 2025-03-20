def create_ui_lnk_on_desktop(name='IGG-Hydrate.lnk'):
    from zmlx.alg.create_shortcut import create_shortcut
    from zmlx import get_path
    from zmlx.alg.get_pythonw_path import get_pythonw_path
    from zmlx.alg.get_desktop_path import get_desktop_path
    create_shortcut(get_pythonw_path(),
                    get_desktop_path(name),
                    arguments=get_path('..', 'zml_ui.pyw')
                    )


if __name__ == '__main__':
    create_ui_lnk_on_desktop()
