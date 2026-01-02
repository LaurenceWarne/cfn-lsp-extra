"""
Test definitions for !GetAtts.
"""
import pytest
from lsprotocol.types import Location
from lsprotocol.types import Position
from lsprotocol.types import Range
from pygls.workspace import TextDocument

from cfn_lsp_extra.decode import decode
from cfn_lsp_extra.definitions.attributes import attribute_definition

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


def test_attribute_definition_for_resource(full_aws_context, document_string):
    document = TextDocument(uri="", source=document_string)
    template_data = decode(document_string, "f.yaml")
    position_att = Position(line=25, character=55)
    position_logical_id = Position(line=25, character=50)
    result_att = attribute_definition(
        template_data, document, position_att, full_aws_context
    )
    result_logical_id = attribute_definition(
        template_data, document, position_logical_id, full_aws_context
    )

    expected = Position(line=4, character=2)
    assert result_att.range.start == expected
    assert result_logical_id.range.start == expected


def test_attribute_definition_not_valid(full_aws_context, document_string):
    document = TextDocument(uri="", source=document_string)
    template_data = decode(document_string, "f.yaml")
    position = Position(line=11, character=26)
    result = attribute_definition(template_data, document, position, full_aws_context)
    assert result is None
