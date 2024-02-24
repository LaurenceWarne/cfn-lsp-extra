"""
Definitions for !Refs.
"""

import logging
from typing import Optional

from lsprotocol.types import Location, Position
from pygls.workspace import Document

from ..aws_data import AWSContext, Tree
from .attributes import attribute_definition
from .ref import ref_definition

logger = logging.getLogger(__name__)


def definition(
    template_data: Tree,
    document: Document,
    position: Position,
    aws_context: AWSContext,
) -> Optional[Location]:
    ref_result = ref_definition(template_data, document, position, aws_context)
    logger.error(ref_result)
    if ref_result:
        return ref_result

    attribute_result = attribute_definition(
        template_data, document, position, aws_context
    )
    logger.error(attribute_result)
    return attribute_result
