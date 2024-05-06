"""
Tests for allowed value completions.
"""
import pytest
from cfn_lsp_extra.completions.allowed_values import allowed_values_completions
from cfn_lsp_extra.decode import decode, decode_unfinished
from cfn_lsp_extra.decode.extractors import ResourcePropertyExtractor
from lsprotocol.types import Position
from pygls.workspace import Document

from ..test_aws_data import full_aws_context


@pytest.fixture
def document_string():
    return """AWSTemplateFormatVersion: '2010-09-09'

Resources:

  ECSService:
    Type: AWS::ECS::Service
    Properties:
      DesiredCount: 1
      LaunchType: FARGA
      NetworkConfiguration:
        AwsvpcConfiguration:
          AssignPublicIp: ENABL"""


@pytest.fixture
def document(document_string):
    return Document(uri="", source=document_string)


@pytest.fixture
def extractor():
    return ResourcePropertyExtractor()


def test_property_allowed_value_completion(
    full_aws_context, document_string, document, extractor
):
    line, char = 8, 23
    tree = decode(document_string, "file.yaml")

    result = allowed_values_completions(
        tree,
        full_aws_context,
        document,
        Position(line=line, character=char),
        extractor,
    )

    assert "FARGATE" in (item.label for item in result.items)


def test_nested_property_allowed_value_completion(
    full_aws_context, document_string, document, extractor
):
    line, char = 11, 31
    tree = decode(document_string, "file.yaml")

    result = allowed_values_completions(
        tree,
        full_aws_context,
        document,
        Position(line=line, character=char),
        extractor,
    )

    assert "ENABLED" in (item.label for item in result.items)


def test_property_allowed_value_completion_no_char(full_aws_context, extractor):
    line, char = 8, 18
    document_string = """AWSTemplateFormatVersion: '2010-09-09'

Resources:

  ECSService:
    Type: AWS::ECS::Service
    Properties:
      DesiredCount: 1
      LaunchType: 
      NetworkConfiguration:
        AwsvpcConfiguration:
          AssignPublicIp: ENABLED"""
    document = Document(uri="", source=document_string)
    position = Position(line=line, character=char)
    tree = decode_unfinished(document_string, "file.yaml", position)

    result = allowed_values_completions(
        tree,
        full_aws_context,
        document,
        position,
        extractor,
    )

    assert "FARGATE" in (item.label for item in result.items)
