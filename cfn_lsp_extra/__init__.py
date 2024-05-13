"""Cfn Lsp Extra."""


# credit https://stackoverflow.com/questions/16891340/remove-a-prefix-from-a-string
# TODO remove when support for Python 3.8 is dropped
def remove_prefix(text: str, prefix: str) -> str:
    """Remove prefix from text if necessary."""
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


# TODO remove when support for Python 3.8 is dropped
def remove_suffix(text: str, suffix: str) -> str:
    """Remove suffix from text if necessary."""
    if text.endswith(suffix):
        return text[: -len(suffix)]
    return text
