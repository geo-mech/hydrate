import os


def get_size_mb(path):
    """
    计算指定路径（文件或文件夹）的总大小，返回以MB为单位的浮点数

    参数：
        path (str): 目标路径（支持文件和文件夹）

    返回：
        float: 路径总大小（MB），异常时返回0.0
    """
    try:
        # 路径有效性验证（综合网页4、网页7的处理逻辑）
        if not os.path.exists(path):
            return 0.0

        # 区分文件/文件夹处理（参考网页9的类型判断）
        if os.path.isfile(path):
            # 单个文件处理（优化网页2的方案）
            return os.path.getsize(path) / (1024 * 1024)
        elif os.path.isdir(path):
            # 文件夹处理（继承原逻辑并优化）
            total_size = 0
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except (OSError, PermissionError):
                        continue
            return total_size / (1024 * 1024)
        else:
            # 特殊文件类型（如符号链接）
            return 0.0

    except:  # 统一异常处理（参考网页6的健壮性设计）
        return 0.0


if __name__ == '__main__':
    print(get_size_mb(path='.'))
