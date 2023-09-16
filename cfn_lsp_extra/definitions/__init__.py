"""
Definitions for !Refs.
"""

from typing import Optional

from lsprotocol.types import Location
from lsprotocol.types import Position
from pygls.workspace import Document

from ..aws_data import AWSContext
from ..aws_data import Tree
from .ref import ref_definition


def definition(
    template_data: Tree,
    document: Document,
    position: Position,
    aws_context: AWSContext,
) -> Optional[Location]:
    return ref_definition(template_data, document, position, aws_context)
