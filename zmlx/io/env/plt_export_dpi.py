from zml import app_data

key = 'plt_export_dpi'


def get_value():
    try:
        plt_export_dpi = float(
            app_data.getenv(
                key=key, encoding='utf-8', default='300', ignore_empty=True))
        assert 50 <= plt_export_dpi <= 3000
        return round(plt_export_dpi)
    except Exception as err:
        print(f'Meet error when load plt_export_dpi: {err}')
        return 300


def set_value(value):
    app_data.setenv(key=key, value=str(value), encoding='utf-8')


def test():
    print(get_value())


if __name__ == '__main__':
    test()
