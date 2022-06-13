import json

import yaml

from ..aws_data import Tree
from .json_decoding import CfnJSONDecoder  # type: ignore[attr-defined]
from .yaml_decoding import SafePositionLoader


class CfnDecodingException(Exception):
    pass


def decode(source: str, filename: str) -> Tree:
    """Deserialise the cloudformation template source into a dictionary.

    Parameters
    ----------
    source : str
        template content, expected to be either json or yaml.
    filename: str
        name of the template file, determined whether source is taken to
        be json or yaml.

    Returns
    -------
    Tree
        A recursive dictionary containing items and positional information
        from source.

    Raises
    ------
    CfnDecodingException
        If json or yaml parsing fails."""
    try:
        if filename.endswith("json"):
            data = json.loads(source, cls=CfnJSONDecoder)
        else:
            data = yaml.load(source, Loader=SafePositionLoader)
    except (
        yaml.scanner.ScannerError,
        yaml.parser.ParserError,
        json.JSONDecodeError,
    ) as e:
        raise CfnDecodingException(f"Error decoding {filename}") from e
    return data


def decode_unfinished(source: str, filename: str, line: int) -> Tree:
    """Deserialise the cloudformation template source into a dictionary.

    If decoding fails, attempt to 'fix' source by making edits to the
    current line.

    Parameters
    ----------
    source : str
        template content, expected to be either json or yaml.
    filename: str
        name of the template file, determined whether source is taken to
        be json or yaml.
    line: int
        The line of the user's cursor

    Returns
    -------
    Tree
        A recursive dictionary containing items and positional information
        from source.

    Raises
    ------
    CfnDecodingException
        If json or yaml parsing fails even after edits."""
    try:
        return decode(source, filename)
    except CfnDecodingException:
        new_source_lst = source.splitlines()
        if filename.endswith("json"):
            new_source_lst[line] = new_source_lst[line].rstrip(":, ") + ': "",'
        else:
            new_source_lst[line] = new_source_lst[line].rstrip() + ":"
        new_source = "\n".join(new_source_lst)
        return decode(new_source, filename)
