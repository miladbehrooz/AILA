def human_join(items: list[str]) -> str:
    """Join a list of strings using commas and an Oxford-style 'and'.
    Args:
        items (list[str]): List of strings to join.
    Returns:
        str: Joined string.
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]
