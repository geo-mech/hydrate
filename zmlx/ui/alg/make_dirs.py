import os


def make_dirs(folder):
    """
    Create folders. When the upper-level directory where the given folder is located does not exist,
    it will be automatically created to ensure that the folder is created successfully
    """
    try:
        if folder is not None:
            if not os.path.isdir(folder):
                os.makedirs(folder, exist_ok=True)
    except:
        pass
