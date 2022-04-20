import json
from typing import TypeVar

import yaml

from .extractors import Extractor
from .json_decoding import CfnJSONDecoder  # type: ignore[attr-defined]
from .position import PositionLookup
from .yaml_decoding import SafePositionLoader


T = TypeVar("T")


class CfnDecodingException(Exception):
    pass


def decode(source: str, filename: str, extractor: Extractor[T]) -> PositionLookup[T]:
    """Return a PositionLookup object containing items from source.

    Parameters
    ----------
    source : str
        template content, expected to be either json or yaml.
    filename: str
        name of the template file, determined whether source is taken to
        be json or yaml.
    extractor: Extractor[T]
        Extractor object used to construct the PositionLookup object
        based on the decoded source.

    Returns
    -------
    PositionLookup[T]
        A PositionLookup object containing items from source.

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
    return extractor.extract(data)
