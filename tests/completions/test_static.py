"""
Tests for resource completions.
"""
import pytest
from cfn_lsp_extra.completions.static import static_completions
from cfn_lsp_extra.decode import decode, decode_unfinished
from lsprotocol.types import Position
from pygls.workspace import TextDocument

from ..test_aws_data import (
    aws_context,
    aws_context_resource_dct,
    aws_property_string,
    aws_resource_string,
)
from .test_completions import document, resource_position


def test_static_completions(aws_context):
    document_string = """AWSTemplateFormatVersion: '2010-09-09'

Resources:

  ECSService:
    Type: AWS::ECS::Service
    De
    Properties:
      DesiredCount: 1
      LaunchType: foo"""
    document = TextDocument(uri="", source=document_string)
    position = Position(line=6, character=5)
    tree = decode_unfinished(document_string, "file.yaml", position)
    result = static_completions(tree, aws_context, document, position, False)
    assert "DeletionPolicy" in map(lambda c: c.label, result.items)
