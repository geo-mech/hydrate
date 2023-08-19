def get_lines(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return len(file.readlines())
    except:
        return 0
