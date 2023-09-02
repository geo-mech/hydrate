from zml import Seepage
from zml import app_data


def show_seepage(filepath):
    model = Seepage(path=filepath)
    app_data.put('seepage', model)
    print(model)
