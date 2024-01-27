class Field:
    """
    Define a three-dimensional field. Make value = f(pos) return data at any position.
    where pos is the coordinate and f is an instance of Field
    """

    class Constant:
        """
        A constant field
        """

        def __init__(self, value):
            """
            construct with the constant value
            """
            self.__value = value

        def __call__(self, *args, **kwargs):
            """
            return the value when call
            """
            return self.__value

    def __init__(self, value):
        """
        create the field. treat it as a constant field when it is not a function(__call__ not defined)
        """
        if hasattr(value, '__call__'):
            self.__field = value
        else:
            self.__field = Field.Constant(value)

    def __call__(self, *args, **kwargs):
        return self.__field(*args, **kwargs)
