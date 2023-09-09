"""
Tests for attribute hovers.
"""
import pytest
from lsprotocol.types import Position
from pygls.workspace import Document

from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.decode import decode
from cfn_lsp_extra.hover.attributes import attribute_hover

from ..test_aws_data import full_aws_context


@pytest.fixture
def document_string():
    return """AWSTemplateFormatVersion: '2010-09-09'

Resources:

  ECSTaskExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - 'ecs-tasks.amazonaws.com'
            Action:
              - 'sts:AssumeRole'
      Path: /
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
      
  ECSTaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Cpu: 256
      Memory: 512
      NetworkMode: awsvpc
      ExecutionRoleArn: !GetAtt ECSTaskExecutionRole.Arn
      ContainerDefinitions:
        - Name: foo
          Image: silex/emacs
          PortMappings:
            - ContainerPort: 80
      RequiresCompatibilities:
        - EC2"""


@pytest.fixture
def document(document_string):
    return Document(uri="", source=document_string)


def test_attribute_hover(
    full_aws_context,
    document_string,
    document,
):
    line, before_dot_char, after_dot_char = 25, 47, 54
    tree = decode(document_string, "file.yaml")

    # Test we get completions in both
    # - !GetAtt ECSTaskExecution<>Role.Arn
    # - !GetAtt ECSTaskExecutionRole.A<>rn
    before_dot_result = attribute_hover(
        tree,
        full_aws_context,
        document,
        Position(line=line, character=before_dot_char),
    )
    after_dot_result = attribute_hover(
        tree,
        full_aws_context,
        document,
        Position(line=line, character=after_dot_char),
    )

    assert "Arn" in before_dot_result.contents.value
    assert "Arn" in after_dot_result.contents.value


def test_no_attribute_hover(
    full_aws_context,
    document_string,
    document,
):
    tree = decode(document_string, "file.yaml")

    result = attribute_hover(
        tree,
        full_aws_context,
        document,
        Position(line=42, character=8),
    )

    assert result is None
