def bbox_is_valid(bbox):
    min_x, min_y, max_x, max_y = bbox
    if (
        min_x > max_x
        or min_x < -180
        or max_x > 180
        or min_y > max_y
        or min_y < -90
        or max_y > 90
    ):
        return False

    return True


def delimit_tuple(tuple_: tuple, delimiter=","):
    """Convert list to delimiter-separated string"""
    if not type(tuple_) == tuple:
        raise TypeError(
            "Expected a list or tuple, " "but got {}".format(type(tuple_).__name__)
        )
    return delimiter.join(map(str, tuple_))
