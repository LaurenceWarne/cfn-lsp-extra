"""
Tests for ref hovers.
"""
import pytest
from lsprotocol.types import Position
from pygls.workspace import TextDocument

from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.decode import decode
from cfn_lsp_extra.hovers.refs import ref_hover

from ..test_aws_data import full_aws_context


@pytest.fixture
def document_string():
    return """AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  BaseStackName:
    Type: String
    Description: Name of the base stack
  LayerKey:
    Type: String
    Description: Name of the S3 key pointing to the lambda layer containg the executable

Resources:

  ExeLambdaLayer:
    Type: AWS::Lambda::LayerVersion
    Properties:
      Content:
        S3Bucket: !ImportValue
          'Fn::Sub': '${BaseStackName}-MiscBucket'
        S3Key: !Ref LayerKey
        
  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      Layers:
        # https://github.com/lambci/git-lambda-layer
        - arn:aws:lambda:us-east-1:553035198032:layer:git-lambda2:8
        - !Ref ExeLambdaLayer
      Role: !GetAtt LambdaFunctionRole.Arn
      Runtime: provided.al2  # Custom runtime
      Handler: bootstrap
      Timeout: 120
      MemorySize: 512  # Probably we can get away with 256"""


@pytest.fixture
def document(document_string):
    return TextDocument(uri="", source=document_string)


def test_ref_resource_hover(
    full_aws_context,
    document_string,
    document,
):
    line, char = 25, 18
    tree = decode(document_string, "file.yaml")

    result = ref_hover(
        tree,
        Position(line=line, character=char),
        full_aws_context,
        document,
    )

    assert "AWS::Lambda::LayerVersion" in result.contents.value


def test_parameter_resource_hover(
    full_aws_context,
    document_string,
    document,
):
    line, char = 17, 25
    tree = decode(document_string, "file.yaml")

    result = ref_hover(
        tree,
        Position(line=line, character=char),
        full_aws_context,
        document,
    )

    assert "LayerKey" in result.contents.value


def test_no_ref_hover(
    full_aws_context,
    document_string,
    document,
):
    tree = decode(document_string, "file.yaml")

    result = ref_hover(
        tree,
        Position(line=42, character=8),
        full_aws_context,
        document,
    )

    assert result is None
