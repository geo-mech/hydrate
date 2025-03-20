import os

def get_latest_file(folder):
    """
    获取指定文件夹内最新修改的文件的绝对路径

    参数：
        folder (str): 目标文件夹路径

    返回：
        str|None: 最新文件的绝对路径，异常时返回None
    """
    try:
        if not os.path.isdir(folder):
            return None

        latest_time = 0
        latest_path = None

        for entry in os.listdir(folder):
            full_path = os.path.join(folder, entry)
            if os.path.isfile(full_path):
                file_time = os.path.getmtime(full_path)
                if file_time > latest_time:
                    latest_time = file_time
                    latest_path = full_path

        return os.path.abspath(latest_path) if latest_path else None

    except:
        return None


if __name__ == '__main__':
    print(get_latest_file(os.path.dirname(__file__)))
