def get_text_back(filename, max_length=None):
    try:
        # 添加errors参数处理解码问题
        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            if max_length is None:
                return file.read()

            file.seek(0, 2)
            file_size = file.tell()
            start_pos = max(0, file_size - max_length)
            file.seek(start_pos)
            return file.read()[-max_length:]

    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return None

if __name__ == '__main__':
    print(get_text_back(__file__, max_length=200))
