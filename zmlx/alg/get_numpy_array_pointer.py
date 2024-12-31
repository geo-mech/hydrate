import numpy as np
import ctypes


def get_numpy_array_pointer(arr):
    """
    Returns the C language pointer to the given NumPy array.
        Since 2024-12-26 by MarsCode AI.
    Args:
        arr (numpy.ndarray): The input NumPy array.
    Returns:
        ctypes.POINTER(ctypes.c_double): The C language pointer to the array.
    """
    # Ensure the input is a NumPy array
    if not isinstance(arr, np.ndarray):
        raise ValueError("Input must be a NumPy array")

    # Get the data type of the array
    dtype = arr.dtype

    # Convert the NumPy array to a C array
    c_arr = np.ctypeslib.as_ctypes(arr)

    # Get the pointer to the C array
    pointer = ctypes.cast(c_arr, ctypes.POINTER(ctypes.c_double if dtype == np.float64 else ctypes.c_float))

    return pointer


if __name__ == '__main__':
    a = np.linspace(0, 3, 10)
    print(a)
    p = get_numpy_array_pointer(a)
    p[2] = 123
    print(a)
