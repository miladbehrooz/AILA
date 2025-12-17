from collections.abc import Generator


def batch(list_: list, size: int) -> Generator[list, None, None]:
    """Yield slices from a list in fixed-size batches.
    Args:
        list_ (list): Source list to batch.
        size (int): Target batch size.
    Yields:
        Generator[list, None, None]: Subsequent list slices of the specified size.
    """
    yield from (list_[i : i + size] for i in range(0, len(list_), size))
