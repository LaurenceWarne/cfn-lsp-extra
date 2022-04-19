import json
from typing import Sequence
from typing import TypeVar

import yaml
from pygls.workspace import Document

from .extractors import Extractor
from .json_decoding import CfnJSONDecoder
from .position import PositionLookup
from .yaml_decoding import SafePositionLoader


T = TypeVar("T")


def decode(source: str, filename: str, extractor: Extractor[T]) -> PositionLookup[T]:
    """Return a PositionLookup object containing items from document."""
    if filename.endswith("json"):
        data = json.loads(source, cls=CfnJSONDecoder)
    else:
        data = yaml.load(source, Loader=SafePositionLoader)
    return extractor.extract(data)
