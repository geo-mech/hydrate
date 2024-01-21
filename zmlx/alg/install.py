import os
import sys


def install(name, folder):
    """
    Add the current folder to python's search path
    """
    pth = os.path.join(os.path.dirname(sys.executable), name)
    if not os.path.isdir(folder):
        return
    if os.path.isfile(pth):
        with open(pth, 'r') as file:
            text = file.read()
            if os.path.isdir(text):
                if os.path.samefile(folder, text):
                    return
    with open(pth, 'w') as file:
        file.write(folder)
    print(f"Succeed Installed: '{folder}' \n       --> '{pth}'")
