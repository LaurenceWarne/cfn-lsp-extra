import json

import yaml
from pygls.lsp.types import Position

from ..aws_data import Tree
from .json_decoding import CfnJSONDecoder  # type: ignore[attr-defined]
from .yaml_decoding import SafePositionLoader


DEBUG_CHAR = "."


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
            data = yaml.load(source, Loader=SafePositionLoader)  # noqa
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise CfnDecodingException(f"Error decoding {filename}") from e
    return data


def decode_unfinished(source: str, filename: str, position: Position) -> Tree:
    """Deserialise the cloudformation template source into a dictionary.

    If decoding fails, attempt to 'fix' source by making edits to the
    current line.  If position is on an empty line, the character at
    position will be set to an '.' (to aid completions).

    Parameters
    ----------
    source : str
        template content, expected to be either json or yaml.
    filename: str
        name of the template file, determined whether source is taken to
        be json or yaml.
    position: Position
        The position of the user's cursor in the document

    Returns
    -------
    Tree
        A recursive dictionary containing items and positional information
        from source.

    Raises
    ------
    CfnDecodingException
        If json or yaml parsing fails even after edits."""
    source_lst = source.splitlines()
    line, char = position.line, position.character
    if not filename.endswith("json"):
        source_lst[line] = yaml_line_enricher(source_lst[line], char)
        source = "\n".join(source_lst)
    try:
        return decode(source, filename)
    except CfnDecodingException:
        if filename.endswith("json"):
            source_lst[line] = source_lst[line].rstrip(":, ") + ': "",'
        else:
            source_lst[line] = source_lst[line].rstrip() + ":"
        source = "\n".join(source_lst)
        return decode(source, filename)


def yaml_line_enricher(line: str, char: int) -> str:
    stripped = line.strip()
    if not stripped:  # Empty line for property
        new_line = line[:char] + DEBUG_CHAR
    elif (
        stripped in ("Type:", "Ref:", "Fn::GetAtt:")
        or stripped.endswith("!Ref")
        or stripped.endswith("!GetAtt")
    ):  # For resource or ref
        new_line = line + DEBUG_CHAR
    else:
        new_line = line
    return new_line
